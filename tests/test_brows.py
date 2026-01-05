import unittest

from src.face_blink import FaceBlinkDetector


class Landmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def make_landmarks():
    return [Landmark(0.0, 0.0) for _ in range(400)]


class BrowTests(unittest.TestCase):
    def test_brow_gap_ratio_scales_with_eye_width(self):
        landmarks = make_landmarks()
        # Left eye corners (width 0.2)
        landmarks[33] = Landmark(0.4, 0.5)
        landmarks[133] = Landmark(0.6, 0.5)
        # Brow above lid: gap 0.1 with eye height 0.1 -> ratio 1.0
        landmarks[105] = Landmark(0.5, 0.4)
        landmarks[159] = Landmark(0.5, 0.5)

        landmarks[145] = Landmark(0.5, 0.6)
        ratio = FaceBlinkDetector._brow_gap_ratio(landmarks, 105, 159, 33, 133, 145)
        self.assertAlmostEqual(ratio, 1.0, places=3)


if __name__ == "__main__":
    unittest.main()
