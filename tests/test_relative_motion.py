import unittest

from src.relative_motion import RelativeMotion


class RelativeMotionTests(unittest.TestCase):
    def test_delta_scaling(self):
        motion = RelativeMotion((100, 100), (1000, 500), sensitivity=2.0)
        dx, dy = motion.update((10, 10))
        self.assertEqual((dx, dy), (0.0, 0.0))

        dx, dy = motion.update((15, 20))
        self.assertEqual(dx, 100.0)
        self.assertEqual(dy, 100.0)

    def test_missing_hand_resets_baseline(self):
        motion = RelativeMotion((100, 100), (1000, 500), sensitivity=2.0)
        self.assertIsNone(motion.update(None))
        motion.update((10, 10))
        motion.update((15, 20))
        self.assertIsNone(motion.update(None))

        dx, dy = motion.update((60, 60))
        self.assertEqual((dx, dy), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
