import unittest

from src.smoother import MotionSmoother


class MotionSmootherTests(unittest.TestCase):
    def test_precision_damping_applies_for_small_steps(self):
        smoother = MotionSmoother(
            max_speed=1000.0,
            damping=0.4,
            precision_radius=10.0,
            precision_damping=0.9,
        )
        smoother.apply(0.0, 0.0, 0.0)
        x, y = smoother.apply(5.0, 0.0, 1.0, precision=True)
        self.assertAlmostEqual(x, 4.5, places=3)
        self.assertAlmostEqual(y, 0.0, places=3)

    def test_default_damping_applies_when_not_precision(self):
        smoother = MotionSmoother(
            max_speed=1000.0,
            damping=0.4,
            precision_radius=10.0,
            precision_damping=0.9,
            micro_radius=3.0,
            micro_damping=0.98,
        )
        smoother.apply(0.0, 0.0, 0.0)
        x, y = smoother.apply(5.0, 0.0, 1.0, precision=False)
        self.assertAlmostEqual(x, 2.0, places=3)
        self.assertAlmostEqual(y, 0.0, places=3)

    def test_micro_damping_applies_for_tiny_steps(self):
        smoother = MotionSmoother(
            max_speed=1000.0,
            damping=0.4,
            precision_radius=10.0,
            precision_damping=0.9,
            micro_radius=3.0,
            micro_damping=0.98,
        )
        smoother.apply(0.0, 0.0, 0.0)
        x, y = smoother.apply(2.0, 0.0, 1.0, precision=True)
        self.assertAlmostEqual(x, 1.96, places=3)
        self.assertAlmostEqual(y, 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
