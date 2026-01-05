import unittest

from src.eye_tracker import EyeTracker


class Landmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def make_landmarks(iris_x, iris_y):
    landmarks = [Landmark(0.0, 0.0) for _ in range(478)]

    # Left eye
    landmarks[33] = Landmark(0.0, iris_y)
    landmarks[133] = Landmark(1.0, iris_y)
    landmarks[159] = Landmark(iris_x, 0.0)
    landmarks[145] = Landmark(iris_x, 1.0)
    for idx in (468, 469, 470, 471, 472):
        landmarks[idx] = Landmark(iris_x, iris_y)

    # Right eye
    landmarks[362] = Landmark(0.0, iris_y)
    landmarks[263] = Landmark(1.0, iris_y)
    landmarks[386] = Landmark(iris_x, 0.0)
    landmarks[374] = Landmark(iris_x, 1.0)
    for idx in (473, 474, 475, 476, 477):
        landmarks[idx] = Landmark(iris_x, iris_y)

    return landmarks


class EyeTrackerTests(unittest.TestCase):
    def test_time_scaled_smoothing(self):
        base = make_landmarks(0.6, 0.6)
        moved = make_landmarks(0.8, 0.8)

        tracker_fast = EyeTracker(smooth_alpha=0.5, gain=1.0, neutral_alpha=0.0, ref_fps=60.0)
        tracker_fast.compute(base, timestamp=0.0)
        out_fast = tracker_fast.compute(moved, timestamp=1.0 / 60.0)

        tracker_slow = EyeTracker(smooth_alpha=0.5, gain=1.0, neutral_alpha=0.0, ref_fps=60.0)
        tracker_slow.compute(base, timestamp=0.0)
        out_slow = tracker_slow.compute(moved, timestamp=2.0 / 60.0)

        self.assertGreater(out_slow[0], out_fast[0])
        self.assertGreater(out_slow[1], out_fast[1])


if __name__ == "__main__":
    unittest.main()
