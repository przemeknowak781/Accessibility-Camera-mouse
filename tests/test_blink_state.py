import unittest

from src.blink_state import BlinkStateMachine


class BlinkStateMachineTests(unittest.TestCase):
    def test_long_blink_triggers_once(self):
        blink = BlinkStateMachine(
            blink_threshold=0.22,
            blink_seconds=0.1,
            cooldown=0.0,
            long_blink_seconds=0.5,
        )
        t = 0.0

        def step(left, right, dt):
            nonlocal t
            t += dt
            return blink.update(left, right, t)

        self.assertEqual(step(0.3, 0.3, 0.0), (None, False))
        blink_type, long_blink = step(0.1, 0.1, 0.12)
        self.assertEqual(blink_type, "BOTH")
        self.assertFalse(long_blink)

        blink_type, long_blink = step(0.1, 0.1, 0.4)
        self.assertIsNone(blink_type)
        self.assertTrue(long_blink)

        blink_type, long_blink = step(0.1, 0.1, 0.2)
        self.assertIsNone(blink_type)
        self.assertFalse(long_blink)

        self.assertEqual(step(0.3, 0.3, 0.1), (None, False))
        blink_type, long_blink = step(0.1, 0.1, 0.12)
        self.assertEqual(blink_type, "BOTH")
        self.assertFalse(long_blink)

    def test_long_blink_requires_both_eyes(self):
        blink = BlinkStateMachine(
            blink_threshold=0.22,
            blink_seconds=0.1,
            cooldown=0.0,
            long_blink_seconds=0.3,
        )
        t = 0.0

        def step(left, right, dt):
            nonlocal t
            t += dt
            return blink.update(left, right, t)

        step(0.1, 0.3, 0.0)
        blink_type, long_blink = step(0.1, 0.3, 0.35)
        self.assertEqual(blink_type, "LEFT")
        self.assertFalse(long_blink)

        step(0.3, 0.3, 0.1)
        step(0.3, 0.1, 0.0)
        blink_type, long_blink = step(0.3, 0.1, 0.35)
        self.assertEqual(blink_type, "RIGHT")
        self.assertFalse(long_blink)


if __name__ == "__main__":
    unittest.main()
