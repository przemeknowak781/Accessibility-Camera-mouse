import time
import cv2
import ctypes
import os

# Enable DPI awareness as early as possible
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # PROCESS_SYSTEM_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from src.config import Config
from src.camera import ThreadedCamera
from src.controller import MouseController
from src.accel import MotionAccelerator
from src.event_log import EventLog
from src.eye_tracker import EyeTracker
from src.face_blink import FaceBlinkDetector
from src.head_motion import HeadMotion
from src.hand_detector import HandDetector
from src.hybrid_motion import HybridMotion
from src.mapper import CoordinateMapper
from src.mouse_driver import MouseDriver
from src.one_euro import OneEuroFilter
from src.frame_schedule import schedule_detectors
from src.camera_watchdog import is_camera_stalled
from src.presets import apply_preset, next_preset_name
from src.relative_motion import RelativeMotion
from src.snap_controller import SnapController
from src.smoother import MotionSmoother
from src.tilt_mapper import TiltMapper
from src.ui import HudRenderer
from src.window_utils import (
    enforce_window_topmost,
    get_mini_window_size,
    get_monitor_layout,
    position_mini_window,
    resize_with_letterbox,
    set_window_topmost,
)
def main():
    active_preset = apply_preset(Config, getattr(Config, "PRESET_NAME", None))
    print(f"Preset: {active_preset}")
    # Load settings from Config
    cam_w = Config.CAM_WIDTH
    cam_h = Config.CAM_HEIGHT
    (screen_w, screen_h, screen_x, screen_y), bounds = get_monitor_layout(
        Config.MONITOR_INDEX
    )

    # Initialize Threaded Camera
    camera = ThreadedCamera(Config.CAM_ID, cam_w, cam_h, backend=Config.CAM_BACKEND)
    camera.start()
    detector = HandDetector(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    face_tracker = None
    if (
        Config.BLINK_ENABLED
        or Config.LONG_BLINK_SECONDS > 0
        or Config.SNAP_TRIGGER_MODE == "BROWS"
        or Config.MOVEMENT_MODE == "HEAD"
    ):
        frame_skip = Config.BLINK_FRAME_SKIP
        if Config.MOVEMENT_MODE == "HEAD":
            frame_skip = Config.HEAD_FRAME_SKIP
        face_tracker = FaceBlinkDetector(
            frame_skip=frame_skip,
            input_size=Config.BLINK_INPUT_SIZE,
            blink_threshold=Config.BLINK_THRESHOLD,
            blink_frames=Config.BLINK_FRAMES,
            cooldown=Config.BLINK_COOLDOWN,
        )
    backend = Config.MOUSE_BACKEND
    if backend == "auto":
        if screen_x != 0 or screen_y != 0 or bounds[0] < 0 or bounds[1] < 0:
            backend = "pynput"
        else:
            backend = "autopy"
    mouse = MouseController(backend=backend)
    if backend == "pynput":
        mouse.set_bounds(*bounds)
    mouse_driver = MouseDriver(mouse)
    mouse_driver.start()
    monitor_label = Config.MONITOR_INDEX if Config.MONITOR_INDEX >= 0 else "primary"
    print(
        f"Using Monitor {monitor_label}: {screen_w}x{screen_h} @ ({screen_x},{screen_y})"
    )
    print(f"Mouse backend: {backend}")
        
    smoother_x = OneEuroFilter(min_cutoff=Config.SMOOTHING_MIN_CUTOFF, beta=Config.SMOOTHING_BETA)
    smoother_y = OneEuroFilter(min_cutoff=Config.SMOOTHING_MIN_CUTOFF, beta=Config.SMOOTHING_BETA)
    motion_smoother = MotionSmoother(
        max_speed=Config.MOTION_MAX_SPEED,
        damping=Config.MOTION_DAMPING,
        precision_radius=Config.HEAD_PRECISION_RADIUS,
        precision_damping=Config.HEAD_PRECISION_DAMPING,
        micro_radius=Config.HEAD_MICRO_RADIUS,
        micro_damping=Config.HEAD_MICRO_DAMPING,
    )
    accelerator = MotionAccelerator(
        min_speed=Config.ACCEL_MIN_SPEED,
        max_speed=Config.ACCEL_MAX_SPEED,
        max_gain=Config.ACCEL_MAX_GAIN,
        exp=Config.ACCEL_EXP,
    )
    head_motion = HeadMotion(
        (screen_w, screen_h),
        (screen_x, screen_y),
        sensitivity=Config.HEAD_SENSITIVITY,
        deadzone=Config.HEAD_DEADZONE,
        min_speed=Config.HEAD_SPEED_MIN,
        max_speed=Config.HEAD_SPEED_MAX,
        exp=Config.HEAD_EXP,
        neutral_alpha=Config.HEAD_NEUTRAL_ALPHA,
        micro_gain=Config.HEAD_MICRO_GAIN,
        stop_threshold=Config.HEAD_STOP_THRESHOLD,
        stop_hold=Config.HEAD_STOP_HOLD,
        return_brake=Config.HEAD_RETURN_BRAKE,
        return_brake_margin=Config.HEAD_RETURN_BRAKE_MARGIN,
        tilt_boost=Config.HEAD_TILT_BOOST,
    )
    eye_tracker = EyeTracker(
        smooth_alpha=Config.EYE_SMOOTH_ALPHA,
        gain=Config.EYE_GAIN,
        neutral_alpha=Config.EYE_NEUTRAL_ALPHA,
        ref_fps=Config.EYE_SMOOTH_FPS_REFERENCE,
    )
    tilt_mapper = TiltMapper(decay=Config.TILT_DECAY, min_range=Config.TILT_MIN_RANGE)
    hybrid_motion = HybridMotion(
        tilt_mapper,
        (screen_w, screen_h),
        (screen_x, screen_y),
        fine_scale=Config.FINE_SCALE,
        fine_weight=Config.FINE_WEIGHT,
        coarse_weight=Config.COARSE_WEIGHT,
    )
    mapper = CoordinateMapper((cam_w, cam_h), (screen_w, screen_h), Config.FRAME_MARGIN, (screen_x, screen_y))
    relative_motion = RelativeMotion(
        (cam_w, cam_h),
        (screen_w, screen_h),
        sensitivity=Config.REL_SENSITIVITY,
    )
    hud = HudRenderer((cam_w, cam_h))
    event_log = EventLog(Config.EVENT_LOG_PATH, Config.EVENT_LOG_MAX)
    
    # GDI overlay for snap target visualization
    from src.snap_overlay import GDIOverlay
    snap_overlay = GDIOverlay()
    snap_overlay.start()
    
    snap_controller = SnapController(mouse_driver, event_log, overlay=snap_overlay)
    def center_cursor(reason, timestamp=None):
        now = time.time() if timestamp is None else float(timestamp)
        center_x = screen_x + screen_w * 0.5
        center_y = screen_y + screen_h * 0.5
        motion_smoother.reset()
        smoother_x.last_time = None
        smoother_y.last_time = None
        mouse_driver.update_target(center_x, center_y, timestamp=now)
        event_log.add(f"CENTER_{reason.upper()}", now)
    def should_exit():
        return cv2.waitKey(1) & 0xFF == 27
    prev_time = time.time()
    last_frame_id = None
    camera_restart_at = 0.0
    prev_brows_raised = False
    def restart_camera(reason, timestamp=None):
        nonlocal camera, last_frame_id, camera_restart_at
        now = time.time() if timestamp is None else float(timestamp)
        if now < camera_restart_at:
            return
        camera_restart_at = now + Config.CAMERA_RESTART_COOLDOWN
        event_log.add(f"CAMERA_RESTART_{reason.upper()}", now)
        print(f"Camera restart ({reason})")
        camera.release()
        camera = ThreadedCamera(Config.CAM_ID, cam_w, cam_h, backend=Config.CAM_BACKEND)
        camera.start()
        last_frame_id = None
    print("Handsteer Started. Press ESC to exit.")
    center_cursor("start", timestamp=prev_time)
    # Spacebar Toggle Logic
    tracking_enabled = True
    movement_mode = Config.MOVEMENT_MODE
    active_preset = getattr(Config, "ACTIVE_PRESET", active_preset)
    mouse_driver.coast_window = Config.COAST_WINDOW if movement_mode == "RELATIVE" else 0.0
    accel_enabled = Config.ACCEL_ENABLED
    accel_max_gain = Config.ACCEL_MAX_GAIN
    accel_min_speed = Config.ACCEL_MIN_SPEED
    accel_max_speed = Config.ACCEL_MAX_SPEED
    accel_exp = Config.ACCEL_EXP
    head_sensitivity = Config.HEAD_SENSITIVITY
    head_deadzone = Config.HEAD_DEADZONE
    head_speed = Config.HEAD_SPEED_MAX
    head_exp = Config.HEAD_EXP
    head_neutral_alpha = Config.HEAD_NEUTRAL_ALPHA
    head_micro_gain = Config.HEAD_MICRO_GAIN
    head_stop_threshold = Config.HEAD_STOP_THRESHOLD
    head_stop_hold = Config.HEAD_STOP_HOLD
    head_fine_scale = Config.HEAD_FINE_SCALE
    hand_fine_scale = Config.HAND_FINE_SCALE
    eye_gain = Config.EYE_GAIN
    eye_smooth = Config.EYE_SMOOTH_ALPHA
    eye_neutral_alpha = Config.EYE_NEUTRAL_ALPHA
    calibration_active = False
    calibration_sampling = False
    calibration_sample_start = 0.0
    calibration_sample_count = 0
    calibration_points = [
        ("BL", "Bottom Left", (0.1, 0.9)),
        ("BR", "Bottom Right", (0.9, 0.9)),
        ("TR", "Top Right", (0.9, 0.1)),
        ("TL", "Top Left", (0.1, 0.1)),
    ]
    calibration_index = 0
    last_gaze = None
    render_enabled = Config.RENDER_ENABLED
    relative_cursor = None
    mini_mode = False
    window_name = "Handsteer"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    from pynput import keyboard
    def on_key_press(key):
        nonlocal tracking_enabled, movement_mode, face_tracker
        nonlocal active_preset
        nonlocal accel_enabled, accel_max_gain, accel_min_speed, accel_max_speed, accel_exp
        nonlocal head_sensitivity, head_deadzone
        nonlocal head_speed, head_exp, head_neutral_alpha
        nonlocal head_micro_gain, head_stop_threshold, head_stop_hold
        nonlocal head_fine_scale, hand_fine_scale
        nonlocal eye_gain, eye_smooth, eye_neutral_alpha
        nonlocal calibration_active, calibration_index, last_gaze
        nonlocal calibration_sampling, calibration_sample_start, calibration_sample_count
        nonlocal render_enabled
        nonlocal relative_cursor
        nonlocal mini_mode
        if key == keyboard.Key.f6:
            active_preset = next_preset_name(active_preset, direction=1)
            apply_preset(Config, active_preset)
            active_preset = getattr(Config, "ACTIVE_PRESET", active_preset)

            accel_enabled = Config.ACCEL_ENABLED
            accel_max_gain = Config.ACCEL_MAX_GAIN
            accel_min_speed = Config.ACCEL_MIN_SPEED
            accel_max_speed = Config.ACCEL_MAX_SPEED
            accel_exp = Config.ACCEL_EXP

            head_sensitivity = Config.HEAD_SENSITIVITY
            head_deadzone = Config.HEAD_DEADZONE
            head_speed = Config.HEAD_SPEED_MAX
            head_exp = Config.HEAD_EXP
            head_neutral_alpha = Config.HEAD_NEUTRAL_ALPHA
            head_micro_gain = Config.HEAD_MICRO_GAIN
            head_stop_threshold = Config.HEAD_STOP_THRESHOLD
            head_stop_hold = Config.HEAD_STOP_HOLD

            eye_gain = Config.EYE_GAIN
            eye_smooth = Config.EYE_SMOOTH_ALPHA
            eye_neutral_alpha = Config.EYE_NEUTRAL_ALPHA

            smoother_x.min_cutoff = Config.SMOOTHING_MIN_CUTOFF
            smoother_y.min_cutoff = Config.SMOOTHING_MIN_CUTOFF
            smoother_x.beta = Config.SMOOTHING_BETA
            smoother_y.beta = Config.SMOOTHING_BETA

            motion_smoother.max_speed = Config.MOTION_MAX_SPEED
            motion_smoother.damping = Config.MOTION_DAMPING
            motion_smoother.precision_radius = Config.HEAD_PRECISION_RADIUS
            motion_smoother.precision_damping = Config.HEAD_PRECISION_DAMPING
            motion_smoother.micro_radius = Config.HEAD_MICRO_RADIUS
            motion_smoother.micro_damping = Config.HEAD_MICRO_DAMPING
            motion_smoother.reset()
            smoother_x.last_time = None
            smoother_y.last_time = None

            head_motion.min_speed = Config.HEAD_SPEED_MIN
            mouse_driver.speed_coeff = Config.MOUSE_SPEED_COEFF

            head_motion.reset()
            accelerator.reset()
            relative_motion.reset()
            relative_cursor = None
            center_cursor("preset")
            print(f"Preset: {active_preset}")
            return
        if key == keyboard.Key.space:
            tracking_enabled = not tracking_enabled
            if tracking_enabled:
                print("Resumed.")
                motion_smoother.reset()
                accelerator.reset()
                head_motion.reset()
                relative_motion.reset()
                relative_cursor = None
                mouse_driver.resume()
            else:
                print("Paused.")
                mouse_driver.pause()
            return

        try:
            if key.char in ('s', 'S'):
                enabled = snap_controller.toggle_enabled()
                print(f"Snap {'ON' if enabled else 'OFF'}")
                return
            if key.char in ('d', 'D'):
                snap_controller.debug_probe()
                return
            if key.char == '0':
                movement_mode = "RELATIVE"
                print("Mode RELATIVE")
                calibration_active = False
                calibration_sampling = False
                calibration_sample_start = 0.0
                calibration_sample_count = 0
                relative_motion.reset()
                relative_cursor = None
                mouse_driver.coast_window = Config.COAST_WINDOW
                center_cursor("mode")
                return
            if key.char == '1':
                movement_mode = "ABSOLUTE"
                print("Mode ABSOLUTE")
                head_motion.reset()
                calibration_active = False
                calibration_sampling = False
                calibration_sample_start = 0.0
                calibration_sample_count = 0
                relative_motion.reset()
                relative_cursor = None
                mouse_driver.coast_window = 0.0
                center_cursor("mode")
                return
            if key.char == '2':
                movement_mode = "HEAD"
                print("Mode HEAD")
                if face_tracker is None:
                    face_tracker = FaceBlinkDetector(
                        frame_skip=Config.HEAD_FRAME_SKIP,
                        input_size=Config.BLINK_INPUT_SIZE,
                        blink_threshold=Config.BLINK_THRESHOLD,
                        blink_frames=Config.BLINK_FRAMES,
                        cooldown=Config.BLINK_COOLDOWN,
                    )
                head_motion.reset()
                calibration_active = False
                calibration_sampling = False
                calibration_sample_start = 0.0
                calibration_sample_count = 0
                relative_motion.reset()
                relative_cursor = None
                mouse_driver.coast_window = 0.0
                center_cursor("mode")
                return
            if key.char == '3':
                movement_mode = "EYE_HYBRID"
                print("Mode EYE_HYBRID")
                if face_tracker is None:
                    face_tracker = FaceBlinkDetector(
                        frame_skip=Config.HEAD_FRAME_SKIP,
                        input_size=Config.BLINK_INPUT_SIZE,
                        blink_threshold=Config.BLINK_THRESHOLD,
                        blink_frames=Config.BLINK_FRAMES,
                        cooldown=Config.BLINK_COOLDOWN,
                    )
                head_motion.reset()
                eye_tracker.reset()
                eye_tracker.start_calibration()
                calibration_active = True
                calibration_index = 0
                calibration_sampling = False
                calibration_sample_start = 0.0
                calibration_sample_count = 0
                relative_motion.reset()
                relative_cursor = None
                mouse_driver.coast_window = 0.0
                center_cursor("mode")
                return
            if key.char == '4':
                movement_mode = "EYE_HAND"
                print("Mode EYE_HAND")
                if face_tracker is None:
                    face_tracker = FaceBlinkDetector(
                        frame_skip=Config.HEAD_FRAME_SKIP,
                        input_size=Config.BLINK_INPUT_SIZE,
                        blink_threshold=Config.BLINK_THRESHOLD,
                        blink_frames=Config.BLINK_FRAMES,
                        cooldown=Config.BLINK_COOLDOWN,
                    )
                eye_tracker.reset()
                eye_tracker.start_calibration()
                calibration_active = True
                calibration_index = 0
                calibration_sampling = False
                calibration_sample_start = 0.0
                calibration_sample_count = 0
                relative_motion.reset()
                relative_cursor = None
                mouse_driver.coast_window = 0.0
                center_cursor("mode")
                return
            if key.char == '5':
                movement_mode = "TILT_HYBRID"
                print("Mode TILT_HYBRID")
                calibration_active = False
                calibration_sampling = False
                calibration_sample_start = 0.0
                calibration_sample_count = 0
                hybrid_motion.reset()
                relative_motion.reset()
                relative_cursor = None
                mouse_driver.coast_window = 0.0
                center_cursor("mode")
                return
            if key.char in ('a', 'A'):
                accel_enabled = not accel_enabled
                print(f"Accel {'ON' if accel_enabled else 'OFF'}")
                return
            if key.char == '[':
                accel_max_gain = max(1.0, accel_max_gain - 0.1)
            if key.char == ']':
                accel_max_gain = min(12.0, accel_max_gain + 0.1)
            if key.char == '-':
                head_sensitivity = max(0.5, head_sensitivity - 0.1)
            if key.char == '=':
                head_sensitivity = min(20.0, head_sensitivity + 0.1)
            if key.char == 'z':
                head_deadzone = max(0.0, head_deadzone - 0.001)
            if key.char == 'x':
                head_deadzone = min(0.2, head_deadzone + 0.001)
            if key.char == ',':
                head_speed = max(200.0, head_speed - 100.0)
            if key.char == '.':
                head_speed = min(8000.0, head_speed + 100.0)
            if key.char == '/':
                head_exp = max(0.3, head_exp - 0.1)
            if key.char == '\\\\':
                head_exp = min(4.0, head_exp + 0.1)
            if key.char == 'n':
                head_neutral_alpha = max(0.01, head_neutral_alpha - 0.01)
            if key.char == 'm':
                head_neutral_alpha = min(0.5, head_neutral_alpha + 0.01)
            if key.char == 'u':
                head_micro_gain = max(0.5, head_micro_gain - 0.1)
            if key.char == 'i':
                head_micro_gain = min(8.0, head_micro_gain + 0.1)
            if key.char == 'j':
                head_stop_threshold = max(0.001, head_stop_threshold - 0.002)
            if key.char == 'k':
                head_stop_threshold = min(0.1, head_stop_threshold + 0.002)
            if key.char == 'o':
                head_stop_hold = max(0.02, head_stop_hold - 0.02)
            if key.char == 'p':
                head_stop_hold = min(1.0, head_stop_hold + 0.02)
            if key.char == 't':
                head_fine_scale = max(0.05, head_fine_scale - 0.05)
            if key.char == 'y':
                head_fine_scale = min(1.0, head_fine_scale + 0.05)
            if key.char == 'l':
                hand_fine_scale = max(0.05, hand_fine_scale - 0.05)
            if key.char == ';':
                hand_fine_scale = min(1.0, hand_fine_scale + 0.05)
            if key.char == 'v':
                eye_gain = max(0.5, eye_gain - 0.1)
            if key.char == 'b':
                eye_gain = min(5.0, eye_gain + 0.1)
            if key.char == 'f':
                eye_smooth = max(0.05, eye_smooth - 0.05)
            if key.char == 'g':
                eye_smooth = min(0.9, eye_smooth + 0.05)
            if key.char == 'q':
                eye_neutral_alpha = max(0.01, eye_neutral_alpha - 0.01)
            if key.char == 'w':
                eye_neutral_alpha = min(0.3, eye_neutral_alpha + 0.01)
            if key.char == 'c' and movement_mode in ("EYE_HYBRID", "EYE_HAND"):
                eye_tracker.start_calibration()
                calibration_active = True
                calibration_index = 0
                calibration_sampling = False
                calibration_sample_start = 0.0
                calibration_sample_count = 0
            if key.char == 'V':
                render_enabled = not render_enabled
                print(f"Preview {'ON' if render_enabled else 'OFF'}")
            if key.char == 'M':
                mini_mode = not mini_mode
                print(f"Mini Mode {'ON' if mini_mode else 'OFF'}")
                if mini_mode:
                    enforce_window_topmost(window_name)
                else:
                    set_window_topmost(window_name, topmost=False)
                if mini_mode:
                    mini_w, mini_h = get_mini_window_size(max_w=320)
                    cv2.resizeWindow(window_name, mini_w, mini_h)
                    position_mini_window(
                        window_name, screen_x, screen_y, screen_w, screen_h, mini_w, mini_h
                    )
                else:
                    cv2.resizeWindow(window_name, cam_w, cam_h)
                return
        except AttributeError:
            if key == keyboard.Key.enter and calibration_active:
                if not calibration_sampling:
                    calibration_sampling = True
                    calibration_sample_start = time.time()
                    calibration_sample_count = 0
            return

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    while True:
        success, frame, frame_id, frame_time = camera.read()
        now_wall = time.time()
        if is_camera_stalled(frame_time, now_wall, Config.CAMERA_STALL_SECONDS):
            restart_camera("stall", timestamp=now_wall)
            if should_exit():
                break
            time.sleep(0.01)
            continue
        if not success:
            # If camera is just starting up, it might send None
            if should_exit():
                break
            time.sleep(0.01)
            continue
        if frame_id == last_frame_id:
            if should_exit():
                break
            time.sleep(0.001)
            continue
        last_frame_id = frame_id
        frame_ts = frame_time if frame_time is not None else now_wall
        now = frame_ts

        # MediaPipe expects RGB, but we work in BGR for OpenCV
        # Flipping for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Only process if enabled
        click_active = False
        screen_coords = None
        probs = {"blink": None, "pinch": None}
        landmarks = []
        gaze = None
        gaze_display = None
        blink_type = None
        long_blink = False
        blink_processed = False
        snap_target = None
        brows_raised = False
        snap_display = None
        frame_rgb = None
        run_hand = False
        run_face = False
        hand_active = False

        if tracking_enabled:
            run_hand, run_face = schedule_detectors(
                movement_mode,
                frame_id,
                Config.BLINK_ENABLED,
                Config.LONG_BLINK_SECONDS > 0
                or Config.SNAP_TRIGGER_MODE == "BROWS",
            )
            run_face = run_face and face_tracker is not None
            hand_active = movement_mode in (
                "ABSOLUTE",
                "RELATIVE",
                "TILT_HYBRID",
                "EYE_HAND",
            )

            if run_hand or run_face:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if run_face:
                blink_type, long_blink = face_tracker.process(
                    frame,
                    frame_ts,
                    rgb=frame_rgb,
                )
                blink_processed = True
            if run_hand:
                detector.find_hands(frame, draw=render_enabled, rgb=frame_rgb)
            if run_hand or (hand_active and detector.results):
                landmarks = detector.find_position(frame)

        index_tip = None
        thumb_tip = None


        # Extract specific landmarks
        for idx, x, y, z in landmarks:
            if idx == 8:
                index_tip = (x, y, z)
            elif idx == 4:
                thumb_tip = (x, y, z)

        if tracking_enabled and (
            index_tip
            or movement_mode in ("HEAD", "EYE_HYBRID", "EYE_HAND", "RELATIVE", "TILT_HYBRID")
        ):
            if movement_mode in ("HEAD", "EYE_HYBRID", "EYE_HAND"):
                if face_tracker is None:
                    face_tracker = FaceBlinkDetector(
                        frame_skip=Config.HEAD_FRAME_SKIP,
                        input_size=Config.BLINK_INPUT_SIZE,
                        blink_threshold=Config.BLINK_THRESHOLD,
                        blink_frames=Config.BLINK_FRAMES,
                        cooldown=Config.BLINK_COOLDOWN,
                    )
                head_motion.sensitivity = head_sensitivity
                head_motion.deadzone = head_deadzone
                head_motion.max_speed = head_speed
                head_motion.exp = head_exp
                head_motion.neutral_alpha = head_neutral_alpha
                head_motion.micro_gain = head_micro_gain
                head_motion.stop_threshold = head_stop_threshold
                head_motion.stop_hold = head_stop_hold
                delta = head_motion.compute(face_tracker.last_landmarks, now)
                if movement_mode == "HEAD":
                    if delta is not None:
                        dx, dy = delta
                        curr_x, curr_y = mouse_driver.get_last_pos()
                        x_target = curr_x + dx
                        y_target = curr_y + dy
                    else:
                        x_target, y_target = None, None
                elif movement_mode == "EYE_HYBRID":
                    eye_tracker.gain = eye_gain
                    eye_tracker.smooth_alpha = eye_smooth
                    eye_tracker.neutral_alpha = eye_neutral_alpha
                    gaze = eye_tracker.compute(face_tracker.last_landmarks, now)
                    last_gaze = gaze
                    if gaze is not None:
                        mapped = eye_tracker.map_to_screen(gaze)
                        gx, gy = mapped if mapped is not None else gaze
                        gaze_display = (gx, gy)
                        base_x = screen_x + gx * screen_w
                        base_y = screen_y + gy * screen_h
                        if delta is not None:
                            dx, dy = delta
                            x_target = base_x + dx * head_fine_scale
                            y_target = base_y + dy * head_fine_scale
                        else:
                            x_target = base_x
                            y_target = base_y
                    elif delta is not None:
                        dx, dy = delta
                        curr_x, curr_y = mouse_driver.get_last_pos()
                        x_target = curr_x + dx
                        y_target = curr_y + dy
                    else:
                        x_target, y_target = None, None
                else:
                    eye_tracker.gain = eye_gain
                    eye_tracker.smooth_alpha = eye_smooth
                    eye_tracker.neutral_alpha = eye_neutral_alpha
                    gaze = eye_tracker.compute(face_tracker.last_landmarks, now)
                    last_gaze = gaze
                    if gaze is not None:
                        mapped = eye_tracker.map_to_screen(gaze)
                        gx, gy = mapped if mapped is not None else gaze
                        gaze_display = (gx, gy)
                        x_target = screen_x + gx * screen_w
                        y_target = screen_y + gy * screen_h
                        if index_tip:
                            x_cam, y_cam, _ = index_tip
                            hand_x, hand_y = mapper.map(x_cam, y_cam)
                            x_target += (hand_x - (screen_x + screen_w * 0.5)) * hand_fine_scale
                            y_target += (hand_y - (screen_y + screen_h * 0.5)) * hand_fine_scale
                    else:
                        x_target, y_target = None, None
            elif movement_mode == "RELATIVE":
                if relative_cursor is None:
                    curr_x, curr_y = mouse_driver.get_last_pos()
                    relative_cursor = [float(curr_x), float(curr_y)]
                hand_pos = None
                if index_tip:
                    hand_pos = (index_tip[0], index_tip[1])
                delta = relative_motion.update(hand_pos)
                if delta is not None:
                    dx, dy = delta
                    relative_cursor[0] += dx
                    relative_cursor[1] += dy
                    relative_cursor[0] = max(
                        screen_x, min(relative_cursor[0], screen_x + screen_w - 1)
                    )
                    relative_cursor[1] = max(
                        screen_y, min(relative_cursor[1], screen_y + screen_h - 1)
                    )
                    x_target, y_target = relative_cursor[0], relative_cursor[1]
                else:
                    x_target, y_target = None, None
            elif movement_mode == "TILT_HYBRID":
                tilt_target = hybrid_motion.compute(landmarks, (cam_w, cam_h))
                if tilt_target is not None:
                    x_target, y_target = tilt_target
                else:
                    x_target, y_target = None, None
            else:
                x_cam, y_cam, _ = index_tip
                x_target, y_target = mapper.map(x_cam, y_cam)

            accelerator.max_gain = accel_max_gain
            accelerator.min_speed = accel_min_speed
            accelerator.max_speed = accel_max_speed
            accelerator.exp = accel_exp

            if movement_mode != "HEAD" and x_target is not None and accel_enabled:
                x_target, y_target = accelerator.apply(x_target, y_target, now)

            # 1. Jitter reduction (Smooth input first)
            if calibration_active:
                x_target = None
                y_target = None

            if x_target is not None:
                x_in = smoother_x.filter(x_target, now)
                y_in = smoother_y.filter(y_target, now)

                x_smooth, y_smooth = motion_smoother.apply(
                    x_in, y_in, now, precision=movement_mode == "HEAD"
                )
                # Clamp to monitor bounds
                x_smooth = max(screen_x, min(x_smooth, screen_x + screen_w - 1))
                y_smooth = max(screen_y, min(y_smooth, screen_y + screen_h - 1))
                mouse_driver.update_target(x_smooth, y_smooth, timestamp=now)
                screen_coords = (x_smooth, y_smooth)

            # Blink Detection
            if face_tracker:
                if run_face and not blink_processed:
                    blink_type, long_blink = face_tracker.process(
                        frame,
                        now,
                        rgb=frame_rgb,
                    )
                    blink_processed = True
                probs["blink"] = face_tracker.last_prob
                if long_blink:
                    center_cursor("long_blink", timestamp=now)
                if run_face and face_tracker.last_landmarks:
                    brows_raised = face_tracker.check_brows_raised(
                        face_tracker.last_landmarks
                    )
                    if brows_raised != prev_brows_raised:
                        event_log.add("BROWS_ON" if brows_raised else "BROWS_OFF", now)
                        prev_brows_raised = brows_raised

            if face_tracker and Config.ENABLE_BLINK_CLICK:
                if blink_type:
                    event_log.add(f"BLINK_{blink_type}", now)

                    should_click = True
                    if blink_type == 'BOTH' and Config.IGNORE_DOUBLE_BLINK:
                        should_click = False

                    if should_click:
                        click_active = mouse.update_blink(True)
                        if click_active:
                            event_log.add("PULSE_CLICK", now)

            # Pinch Detection
            if thumb_tip and Config.ENABLE_PINCH_CLICK:
                # Euclidean distance for basic pinch check
                dist = np.hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1])

                # Check Z-depth difference to avoid false clicks when fingers overlap in 2D but are apart in 3D
                depth_gap = abs(index_tip[2] - thumb_tip[2])
                if depth_gap > Config.CLICK_DEPTH_THRESHOLD:
                    dist = Config.CLICK_THRESHOLD * 2.0  # Force no-click

                probs["pinch"] = max(
                    0.0, min(1.0, 1.0 - (dist / Config.CLICK_THRESHOLD))
                )
                drag_active = mouse.update_drag(dist)
                if drag_active and not click_active:
                    event_log.add("PINCH_DRAG", now)

                # OR logic: Click if Blink OR pinch drag active
                click_active = click_active or drag_active

            if calibration_active and calibration_sampling:
                if last_gaze is not None:
                    label, _, _ = calibration_points[calibration_index]
                    eye_tracker.add_calibration_sample(label, last_gaze)
                    calibration_sample_count += 1

                elapsed = now - calibration_sample_start
                if (
                    elapsed >= Config.EYE_CALIBRATION_SECONDS
                    and calibration_sample_count >= Config.EYE_CALIBRATION_MIN_SAMPLES
                ):
                    calibration_sampling = False
                    calibration_index += 1
                    if calibration_index >= len(calibration_points):
                        calibration_active = not eye_tracker.finish_calibration()
                        calibration_index = 0
        else:
            accelerator.reset()

        snap_controller.update_active(brows_raised, now)
        snap_pos = screen_coords if screen_coords is not None else mouse_driver.get_last_pos()
        snap_controller.update_cursor_pos(*snap_pos)
        snap_target = snap_controller.sync_target()
        if snap_target is not None:
            snap_display = (
                (snap_target[0] - screen_x) / max(screen_w, 1),
                (snap_target[1] - screen_y) / max(screen_h, 1),
            )
        # Draw HUD even if disabled, but show PAUSED
        now = frame_ts
        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now

        tune = []
        tune.append(
            ("Snap", f"{'on' if snap_controller.enabled else 'off'}", ["S"])
        )
        tune.append(("Preset", f"{active_preset}", ["F6"]))
        tune.append(("Mode", f"{movement_mode}", ["0", "1", "2", "3", "4", "5"]))
        tune.append(("Accel", f"{'on' if accel_enabled else 'off'}", ["A"]))
        tune.append(("Gain", f"{accel_max_gain:.2f}", ["[", "]"]))
        if movement_mode == "HEAD":
            tune.append(("HeadSens", f"{head_sensitivity:.2f}", ["-", "="]))
            tune.append(("Deadzone", f"{head_deadzone:.3f}", ["z", "x"]))
            tune.append(("Speed", f"{head_speed:.0f}", [",", "."]))
            tune.append(("Exp", f"{head_exp:.2f}", ["/", "\\"]))
            tune.append(("Neutral", f"{head_neutral_alpha:.2f}", ["n", "m"]))
            tune.append(("MicroGain", f"{head_micro_gain:.2f}", ["u", "i"]))
            tune.append(("StopTh", f"{head_stop_threshold:.3f}", ["j", "k"]))
            tune.append(("StopHold", f"{head_stop_hold:.2f}", ["o", "p"]))
        if movement_mode == "EYE_HYBRID":
            tune.append(("HeadFine", f"{head_fine_scale:.2f}", ["t", "y"]))
            tune.append(("EyeGain", f"{eye_gain:.2f}", ["v", "b"]))
            tune.append(("EyeSmooth", f"{eye_smooth:.2f}", ["f", "g"]))
            tune.append(("EyeNeutral", f"{eye_neutral_alpha:.2f}", ["q", "w"]))
        if movement_mode == "EYE_HAND":
            tune.append(("HandFine", f"{hand_fine_scale:.2f}", ["l", ";"]))
            tune.append(("EyeGain", f"{eye_gain:.2f}", ["v", "b"]))
            tune.append(("EyeSmooth", f"{eye_smooth:.2f}", ["f", "g"]))
            tune.append(("EyeNeutral", f"{eye_neutral_alpha:.2f}", ["q", "w"]))
            tune.append(("Calib", "ENTER", ["c", "Enter"]))
            # MinGain removed (HEAD_MIN_GAIN no longer used)

        calibration = None
        if calibration_active and movement_mode in ("EYE_HYBRID", "EYE_HAND"):
            _, name, target = calibration_points[calibration_index]
            status = None
            if calibration_sampling:
                elapsed = now - calibration_sample_start
                remaining = max(0.0, Config.EYE_CALIBRATION_SECONDS - elapsed)
                status = (
                    f"Hold still on {name}: {remaining:.1f}s "
                    f"({calibration_sample_count}/{Config.EYE_CALIBRATION_MIN_SAMPLES})"
                )
            calibration = (
                name,
                target,
                calibration_index + 1,
                len(calibration_points),
                status,
            )

        if render_enabled:
            hud.draw_hud(
                frame,
                fps,
                click_active,
                screen_coords,
                event_log.recent(),
                probs,
                paused=not tracking_enabled,
                mode_label=movement_mode,
                tune=tune,
                gaze=gaze_display,
                calibration=calibration,
                snap_target=snap_display,
                snap_active=snap_controller.active,
            )

            if mini_mode:
                mini_w, mini_h = get_mini_window_size(max_w=320)
                display_frame = resize_with_letterbox(frame, mini_w, mini_h)
                color = (0, 255, 0) if tracking_enabled else (0, 0, 255)
                cv2.rectangle(display_frame, (0, 0), (mini_w - 1, mini_h - 1), color, 4)
                cv2.imshow(window_name, display_frame)
                position_mini_window(
                    window_name, screen_x, screen_y, screen_w, screen_h, mini_w, mini_h
                )
                enforce_window_topmost(window_name)
            else:
                cv2.imshow(window_name, frame)
        # Keep CV2 waitKey for window interaction (ESC to quit)
        if should_exit():
            break
        if not render_enabled:
            time.sleep(0.001)

    listener.stop()
    mouse_driver.stop()
    snap_controller.stop()
    snap_overlay.stop()
    camera.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to Exit...")
