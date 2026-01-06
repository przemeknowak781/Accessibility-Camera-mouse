from dataclasses import dataclass

@dataclass
class Config:
    # Tuning preset: "precision", "balanced", "fast", "turbo", "swift", "snappy", "stable", "legacy"
    PRESET_NAME: str = "swift"

    # Camera Settings
    CAM_WIDTH: int = 640
    CAM_HEIGHT: int = 480
    CAM_ID: int = 0
    CAM_BACKEND: str = "auto" # "auto", "msmf", "dshow"
    CAMERA_STALL_SECONDS: float = 1.0
    CAMERA_RESTART_COOLDOWN: float = 2.0
    MONITOR_INDEX: int = -1
    MOUSE_BACKEND: str = "auto"  # "auto", "autopy", "pynput"
    MODEL_DOWNLOAD_TIMEOUT: float = 12.0
    
    # Mapper Settings
    FRAME_MARGIN: int = 100
    
    # Interaction Settings
    CLICK_THRESHOLD: float = 30.0
    CLICK_DEPTH_THRESHOLD: float = 0.08
    CLICK_COOLDOWN: float = 0.2
    
    # Feature Toggles
    ENABLE_PINCH_CLICK: bool = True
    ENABLE_BLINK_CLICK: bool = True 
    IGNORE_DOUBLE_BLINK: bool = True # Ignore if both eyes blink (natural blink)

    # Blink/Wink Settings
    BLINK_ENABLED: bool = True
    BLINK_THRESHOLD: float = 0.22 # For double blink detection
    WINK_THRESHOLD: float = 0.22 # For single eye wink
    BLINK_FRAMES: int = 2 # Min closed duration in frames at BLINK_FPS_REFERENCE
    BLINK_FPS_REFERENCE: float = 60.0
    BLINK_COOLDOWN: float = 0.4
    BLINK_FRAME_SKIP: int = 2
    BLINK_INPUT_SIZE: tuple = (320, 180)
    LONG_BLINK_SECONDS: float = 0.7 # Hold both eyes closed to center cursor

    # Smart Snapping - "Gravity Well" magnetic attraction
    SNAP_ENABLED: bool = True
    SNAP_TRIGGER_MODE: str = "ALWAYS" # "BROWS" or "ALWAYS"
    SNAP_RADIUS: float = 80.0  # Larger magnet range
    SNAP_STRENGTH: float = 0.7  # Stronger attraction (was 0.5)
    SNAP_LOCK_RADIUS: float = 18.0  # Lock when very close
    SNAP_LOCK_STRENGTH: float = 0.98
    SNAP_BREAKOUT_SPEED: float = 80.0  # Speed to break free
    SNAP_INTERVAL: float = 0.05  # Faster scanning
    SNAP_TARGET_HOLD_SECONDS: float = 0.12
    SNAP_BROW_HOLD_SECONDS: float = 0.5
    BROWS_THRESHOLD: float = 1.2
    
    # Movement Settings
    MOVEMENT_MODE: str = "HEAD" # "ABSOLUTE", "RELATIVE", "TILT_HYBRID", "HEAD", "EYE_HYBRID", "EYE_HAND"
    REL_SENSITIVITY: float = 2.0 # Sensitivity for relative movement
    COAST_WINDOW: float = 0.4 # Seconds to coast after losing tracking
    TILT_DECAY: float = 0.006
    TILT_MIN_RANGE: float = 0.18
    FINE_SCALE: float = 0.16
    FINE_WEIGHT: float = 0.9
    COARSE_WEIGHT: float = 1.0
    
    # Mouse Acceleration (higher speed => higher gain)
    ACCEL_ENABLED: bool = True
    ACCEL_MIN_SPEED: float = 180.0
    ACCEL_MAX_SPEED: float = 1600.0
    ACCEL_MAX_GAIN: float = 4.0
    ACCEL_EXP: float = 1.4

    # Head Motion
    HEAD_SENSITIVITY: float = 6.0
    HEAD_DEADZONE: float = 0.005
    HEAD_FRAME_SKIP: int = 0
    HEAD_SPEED_MIN: float = 0.0
    HEAD_SPEED_MAX: float = 2600.0
    HEAD_EXP: float = 1.6
    HEAD_NEUTRAL_ALPHA: float = 0.05
    HEAD_MICRO_GAIN: float = 0.7
    HEAD_STOP_THRESHOLD: float = 0.030
    HEAD_STOP_HOLD: float = 0.34
    HEAD_FINE_SCALE: float = 0.35
    HAND_FINE_SCALE: float = 0.25
    HEAD_RETURN_BRAKE: float = 0.6 # Damp return-to-neutral movement
    HEAD_RETURN_BRAKE_MARGIN: float = 0.01
    HEAD_TILT_BOOST: float = 0.4 # Extra speed when head tilt is large
    HEAD_PRECISION_RADIUS: float = 16.0 # Pixels from target to tighten damping
    HEAD_PRECISION_DAMPING: float = 0.9 # Higher damping for easier stops
    HEAD_MICRO_RADIUS: float = 6.0 # Pixels from target for maximum precision
    HEAD_MICRO_DAMPING: float = 0.98 # Near-snap for micro adjustments
    
    # Eye Tracking
    EYE_SMOOTH_ALPHA: float = 0.35
    EYE_GAIN: float = 2.2
    EYE_NEUTRAL_ALPHA: float = 0.05
    EYE_SMOOTH_FPS_REFERENCE: float = 60.0
    EYE_CALIBRATION_SECONDS: float = 1.2
    EYE_CALIBRATION_MIN_SAMPLES: int = 20

    # Rendering
    RENDER_ENABLED: bool = True
    
    EVENT_LOG_PATH: str = "events.log"
    EVENT_LOG_MAX: int = 8
    MOTION_MAX_SPEED: float = 2200.0
    MOTION_DAMPING: float = 0.4
    
    # Smoothing Settings
    SMOOTHING_MIN_CUTOFF: float = 0.6
    SMOOTHING_BETA: float = 0.003
    
    
    # UI Colors (BGR)
    COLOR_ACCENT: tuple = (0, 208, 255)      # Orange/Gold
    COLOR_ACCENT_2: tuple = (96, 255, 168)   # Green/Teal
    COLOR_DARK: tuple = (18, 20, 28)         # Dark Background
    COLOR_LIGHT: tuple = (236, 238, 242)     # White/Light Text
    COLOR_DRAW_HAND: tuple = (0, 255, 180) 
    COLOR_DRAW_LINE: tuple = (255, 255, 255)

    # Mouse Driver Settings
    MOUSE_REFRESH_RATE: int = 120
    MOUSE_FRICTION: float = 0.92
    MOUSE_SPEED_COEFF: float = 35.0
    MOUSE_OVERRIDE_DIST: float = 80.0 # Pixels moved by user to trigger override
    MOUSE_OVERRIDE_TIMEOUT: float = 1.0 # Seconds to wait before reclaiming control
