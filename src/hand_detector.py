import cv2
import importlib
import os
from src.config import Config
from src.model_utils import download_model


class HandDetector:
    def __init__(
        self,
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
        model_path="models/hand_landmarker.task",
    ):
        self.static_image_mode = static_image_mode
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_path = model_path

        self._ensure_model()
        self._load_modules()
        self._init_landmarker()
        self.results = None

    def _ensure_model(self):
        if os.path.exists(self.model_path):
            return
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        url = (
            "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
            "hand_landmarker/float16/1/hand_landmarker.task"
        )
        print("Downloading hand model...")
        download_model(url, self.model_path, timeout=Config.MODEL_DOWNLOAD_TIMEOUT)

    def _load_modules(self):
        self.mp_image = importlib.import_module(
            "mediapipe.tasks.python.vision.core.image"
        )
        self.base_options = importlib.import_module(
            "mediapipe.tasks.python.core.base_options"
        )
        self.hand_landmarker_module = importlib.import_module(
            "mediapipe.tasks.python.vision.hand_landmarker"
        )

        self._connections = []
        for name in dir(self.hand_landmarker_module.HandLandmarksConnections):
            if name.endswith("_CONNECTIONS"):
                connections = getattr(
                    self.hand_landmarker_module.HandLandmarksConnections, name
                )
                for conn in connections:
                    self._connections.append((conn.start, conn.end))

    def _init_landmarker(self):
        options = self.hand_landmarker_module.HandLandmarkerOptions(
            base_options=self.base_options.BaseOptions(model_asset_path=self.model_path),
            num_hands=self.max_num_hands,
            min_hand_detection_confidence=self.min_detection_confidence,
            min_hand_presence_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        )
        self.landmarker = self.hand_landmarker_module.HandLandmarker.create_from_options(
            options
        )

    def find_hands(self, frame, draw=True, rgb=None):
        rgb_frame = rgb if rgb is not None else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = self.mp_image.Image(self.mp_image.ImageFormat.SRGB, rgb_frame)
        self.results = self.landmarker.detect(mp_img)
        if draw and self.results.hand_landmarks:
            self._draw_landmarks(frame, self.results.hand_landmarks)
        return frame

    def _draw_landmarks(self, frame, hand_landmarks):
        h, w, _ = frame.shape
        for hand in hand_landmarks:
            points = []
            for lm in hand:
                cx, cy = int(lm.x * w), int(lm.y * h)
                points.append((cx, cy))
                cv2.circle(frame, (cx, cy), 3, (0, 255, 180), -1)
            for start, end in self._connections:
                cv2.line(frame, points[start], points[end], (255, 255, 255), 1)

    def find_position(self, frame, hand_index=0):
        landmark_list = []
        if not self.results or not self.results.hand_landmarks:
            return landmark_list

        hand = self.results.hand_landmarks[hand_index]
        h, w, _ = frame.shape
        for idx, lm in enumerate(hand):
            cx, cy = int(lm.x * w), int(lm.y * h)
            landmark_list.append((idx, cx, cy, lm.z))
        return landmark_list
