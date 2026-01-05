import unittest

from src.hybrid_motion import HybridMotion
from src.tilt_mapper import TiltMapper


class HybridMotionTests(unittest.TestCase):
    def test_compute_returns_expected_target(self):
        tilt_mapper = TiltMapper(decay=0.005, min_range=0.15)
        motion = HybridMotion(
            tilt_mapper,
            (1000, 500),
            (0, 0),
            fine_scale=0.18,
            fine_weight=1.0,
            coarse_weight=1.0,
        )

        landmarks = [
            (0, 0.0, 0.0, 0.0),
            (5, 1.0, 0.0, 0.0),
            (17, 0.0, 1.0, 0.0),
            (8, 1.0, 1.0, 0.0),
        ]

        x_target, y_target = motion.compute(landmarks, (100, 100))
        self.assertAlmostEqual(x_target, 584.8528, places=3)
        self.assertAlmostEqual(y_target, 292.4264, places=3)


if __name__ == "__main__":
    unittest.main()
