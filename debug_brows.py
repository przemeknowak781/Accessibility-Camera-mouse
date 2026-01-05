import time

import cv2

from src.camera import ThreadedCamera
from src.config import Config
from src.face_blink import FaceBlinkDetector


def main():
    cam = ThreadedCamera(Config.CAM_ID, Config.CAM_WIDTH, Config.CAM_HEIGHT)
    cam.start()

    face = FaceBlinkDetector(
        frame_skip=0,
        input_size=Config.BLINK_INPUT_SIZE,
        blink_threshold=Config.BLINK_THRESHOLD,
        blink_frames=Config.BLINK_FRAMES,
        cooldown=Config.BLINK_COOLDOWN,
    )
    print("Press ESC to quit.")
    last_frame_id = None

    while True:
        success, frame, frame_id, frame_time = cam.read()
        if not success or frame is None:
            time.sleep(0.01)
            continue
        if frame_id == last_frame_id:
            time.sleep(0.001)
            continue
        last_frame_id = frame_id
        now = frame_time if frame_time is not None else time.time()
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _, _ = face.process(frame, now, rgb=frame_rgb)

        ratio = None
        if face.last_landmarks:
            ratio = face.brow_ratio(face.last_landmarks)
        text = f"Brow ratio: {ratio:.3f}" if ratio is not None else "No face"
        cv2.putText(
            frame,
            text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow("Brow Debug", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

