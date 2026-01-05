import importlib
import os
from src.blink_state import BlinkStateMachine
from src.config import Config
from src.model_utils import download_model

import cv2
import numpy as np


class FaceBlinkDetector:
    def __init__(
        self,
        model_path="models/face_landmarker.task",
        frame_skip=2,
        input_size=(320, 180),
        blink_threshold=0.22,
        blink_frames=2,
        cooldown=0.4,
    ):
        self.model_path = model_path
        self.frame_skip = max(int(frame_skip), 0)
        self.input_size = input_size
        self.blink_threshold = float(blink_threshold)
        self.blink_frames = max(int(blink_frames), 1)
        self.cooldown = float(cooldown)
        self._blink_time = self.blink_frames / max(Config.BLINK_FPS_REFERENCE, 1.0)
        self._blink_state = BlinkStateMachine(
            blink_threshold=self.blink_threshold,
            blink_seconds=self._blink_time,
            cooldown=self.cooldown,
            long_blink_seconds=Config.LONG_BLINK_SECONDS,
        )

        self._frame_count = 0
        self.last_ratio = None
        self.last_prob = 0.0
        self.last_landmarks = None

        self._ensure_model()
        self._load_modules()
        self._init_landmarker()

        self._left_eye = {"left": 33, "right": 133, "upper": 159, "lower": 145}
        self._right_eye = {"left": 362, "right": 263, "upper": 386, "lower": 374}
        self._brow_left = 105
        self._brow_right = 334
        self._lid_left = 159
        self._lid_right = 386
        self._lower_left = 145
        self._lower_right = 374

    def _ensure_model(self):
        if os.path.exists(self.model_path):
            return
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        url = (
            "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
            "face_landmarker/float16/1/face_landmarker.task"
        )
        print("Downloading face model...")
        download_model(url, self.model_path, timeout=Config.MODEL_DOWNLOAD_TIMEOUT)

    def _load_modules(self):
        self.mp_image = importlib.import_module(
            "mediapipe.tasks.python.vision.core.image"
        )
        self.base_options = importlib.import_module(
            "mediapipe.tasks.python.core.base_options"
        )
        self.face_landmarker_module = importlib.import_module(
            "mediapipe.tasks.python.vision.face_landmarker"
        )

    def _init_landmarker(self):
        options = self.face_landmarker_module.FaceLandmarkerOptions(
            base_options=self.base_options.BaseOptions(model_asset_path=self.model_path),
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self.landmarker = self.face_landmarker_module.FaceLandmarker.create_from_options(
            options
        )

    def reset(self):
        self._blink_state.reset()
        self.last_ratio = None
        self.last_prob = 0.0
        self.last_landmarks = None

    def process(self, frame, timestamp, rgb=None):
        if self.frame_skip and (self._frame_count % (self.frame_skip + 1)) != 0:
            self._frame_count += 1
            return None, False
        self._frame_count += 1

        rgb_frame = rgb if rgb is not None else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.input_size:
            rgb_frame = cv2.resize(rgb_frame, self.input_size, interpolation=cv2.INTER_AREA)

        mp_img = self.mp_image.Image(self.mp_image.ImageFormat.SRGB, rgb_frame)
        result = self.landmarker.detect(mp_img)
        if not result.face_landmarks:
            self.reset()
            return None, False

        landmarks = result.face_landmarks[0]
        self.last_landmarks = landmarks
        left_ratio = self._ratio_for_eye(landmarks, self._left_eye)
        right_ratio = self._ratio_for_eye(landmarks, self._right_eye)
        
        # Store for visualization
        self.last_ratio = (left_ratio + right_ratio) / 2
        self.last_prob = max(0.0, min(1.0, 1.0 - (self.last_ratio / self.blink_threshold))) # Avg prob

        blink_type, long_blink = self._blink_state.update(
            left_ratio,
            right_ratio,
            timestamp,
        )
        return blink_type, long_blink

    def _eye_ratio(self, landmarks):
        left = self._ratio_for_eye(landmarks, self._left_eye)
        right = self._ratio_for_eye(landmarks, self._right_eye)
        return (left + right) * 0.5

    def brow_ratio(self, landmarks):
        left = self._brow_gap_ratio(
            landmarks,
            self._brow_left,
            self._lid_left,
            self._left_eye["left"],
            self._left_eye["right"],
            self._lower_left,
        )
        right = self._brow_gap_ratio(
            landmarks,
            self._brow_right,
            self._lid_right,
            self._right_eye["left"],
            self._right_eye["right"],
            self._lower_right,
        )
        return (left + right) * 0.5

    def check_brows_raised(self, landmarks):
        return self.brow_ratio(landmarks) >= Config.BROWS_THRESHOLD

    def _ratio_for_eye(self, landmarks, idx):
        left = landmarks[idx["left"]]
        right = landmarks[idx["right"]]
        upper = landmarks[idx["upper"]]
        lower = landmarks[idx["lower"]]

        h = np.hypot(left.x - right.x, left.y - right.y)
        v = np.hypot(upper.x - lower.x, upper.y - lower.y)
        if h <= 1e-6:
            return 1.0
        return v / h

    @staticmethod
    def _brow_gap_ratio(landmarks, brow_idx, lid_idx, left_idx, right_idx, lower_idx):
        brow = landmarks[brow_idx]
        lid = landmarks[lid_idx]
        lower = landmarks[lower_idx]
        left = landmarks[left_idx]
        right = landmarks[right_idx]
        eye_w = np.hypot(left.x - right.x, left.y - right.y)
        eye_h = abs(lid.y - lower.y)
        scale = max(eye_h, eye_w * 0.25)
        if scale <= 1e-6:
            return 0.0
        gap = lid.y - brow.y
        return max(0.0, gap / scale)
