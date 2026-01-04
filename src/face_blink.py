import importlib
import os
import urllib.request

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

        self._frame_count = 0
        self._closed_frames = 0
        self._ready = True
        self._last_blink_time = 0.0
        self.last_ratio = None
        self.last_prob = 0.0
        self.last_landmarks = None

        self._ensure_model()
        self._load_modules()
        self._init_landmarker()

        self._left_eye = {"left": 33, "right": 133, "upper": 159, "lower": 145}
        self._right_eye = {"left": 362, "right": 263, "upper": 386, "lower": 374}

    def _ensure_model(self):
        if os.path.exists(self.model_path):
            return
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        url = (
            "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
            "face_landmarker/float16/1/face_landmarker.task"
        )
        urllib.request.urlretrieve(url, self.model_path)

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
        self._closed_frames = 0
        self._ready = True
        self.last_ratio = None
        self.last_prob = 0.0
        self.last_landmarks = None

    def process(self, frame, timestamp):
        if self.frame_skip and (self._frame_count % (self.frame_skip + 1)) != 0:
            self._frame_count += 1
            return None
        self._frame_count += 1

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.input_size:
            rgb = cv2.resize(rgb, self.input_size, interpolation=cv2.INTER_AREA)

        mp_img = self.mp_image.Image(self.mp_image.ImageFormat.SRGB, rgb)
        result = self.landmarker.detect(mp_img)
        if not result.face_landmarks:
            self.reset()
            return None

        landmarks = result.face_landmarks[0]
        self.last_landmarks = landmarks
        left_ratio = self._ratio_for_eye(landmarks, self._left_eye)
        right_ratio = self._ratio_for_eye(landmarks, self._right_eye)
        
        # Store for visualization
        self.last_ratio = (left_ratio + right_ratio) / 2
        self.last_prob = max(0.0, min(1.0, 1.0 - (self.last_ratio / self.blink_threshold))) # Avg prob

        # Check states
        left_closed = left_ratio < self.blink_threshold
        right_closed = right_ratio < self.blink_threshold
        
        # Determine current state
        state = None
        if left_closed and right_closed:
            state = 'BOTH'
        elif left_closed:
            state = 'LEFT'
        elif right_closed:
            state = 'RIGHT'
            
        # State Machine / Debounce
        detected = None
        if state:
            self._closed_frames += 1
            if self._ready and self._closed_frames >= self.blink_frames:
                if (timestamp - self._last_blink_time) > self.cooldown:
                    # Valid Trigger
                    self._last_blink_time = timestamp
                    self._ready = False
                    detected = state
        else:
            # Reset if eyes open (hysteresis could be added here)
            if not left_closed and not right_closed: # Wait for both to be fully open
                 if left_ratio > self.blink_threshold * 1.1 and right_ratio > self.blink_threshold * 1.1:
                    self._closed_frames = 0
                    self._ready = True
                    
        return detected

    def _eye_ratio(self, landmarks):
        left = self._ratio_for_eye(landmarks, self._left_eye)
        right = self._ratio_for_eye(landmarks, self._right_eye)
        return (left + right) * 0.5

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
