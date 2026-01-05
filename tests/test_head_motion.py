import unittest

from src.head_motion import HeadMotion


class Landmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def make_landmarks(raw_dx, raw_dy):
    landmarks = [
        Landmark(0.0, 0.0),  # idx 0
        Landmark(0.5 + raw_dx, 0.5 + raw_dy),  # idx 1 (nose)
        Landmark(1.0, 0.0),
        Landmark(0.0, 1.0),
        Landmark(1.0, 1.0),
    ]
    return landmarks


class HeadMotionTests(unittest.TestCase):
    def test_return_brake_reduces_speed(self):
        base = HeadMotion(
            (1920, 1080),
            (0, 0),
            sensitivity=1.0,
            deadzone=0.0,
            min_speed=0.0,
            max_speed=100.0,
            exp=1.0,
            neutral_alpha=0.0,
            micro_gain=1.0,
            stop_threshold=0.0,
            stop_hold=0.0,
            return_brake=1.0,
            return_brake_margin=0.0,
            tilt_boost=0.0,
        )
        brake = HeadMotion(
            (1920, 1080),
            (0, 0),
            sensitivity=1.0,
            deadzone=0.0,
            min_speed=0.0,
            max_speed=100.0,
            exp=1.0,
            neutral_alpha=0.0,
            micro_gain=1.0,
            stop_threshold=0.0,
            stop_hold=0.0,
            return_brake=0.5,
            return_brake_margin=0.0,
            tilt_boost=0.0,
        )

        base.compute(make_landmarks(0.0, 0.0), 0.0)
        brake.compute(make_landmarks(0.0, 0.0), 0.0)

        base.compute(make_landmarks(0.3, 0.0), 1.0)
        brake.compute(make_landmarks(0.3, 0.0), 1.0)

        base_dx, _ = base.compute(make_landmarks(0.1, 0.0), 2.0)
        brake_dx, _ = brake.compute(make_landmarks(0.1, 0.0), 2.0)

        self.assertLess(abs(brake_dx), abs(base_dx))

    def test_tilt_boost_increases_speed(self):
        slow = HeadMotion(
            (1920, 1080),
            (0, 0),
            sensitivity=1.0,
            deadzone=0.0,
            min_speed=0.0,
            max_speed=100.0,
            exp=1.0,
            neutral_alpha=0.0,
            micro_gain=1.0,
            stop_threshold=0.0,
            stop_hold=0.0,
            return_brake=1.0,
            return_brake_margin=0.0,
            tilt_boost=0.0,
        )
        boosted = HeadMotion(
            (1920, 1080),
            (0, 0),
            sensitivity=1.0,
            deadzone=0.0,
            min_speed=0.0,
            max_speed=100.0,
            exp=1.0,
            neutral_alpha=0.0,
            micro_gain=1.0,
            stop_threshold=0.0,
            stop_hold=0.0,
            return_brake=1.0,
            return_brake_margin=0.0,
            tilt_boost=0.5,
        )

        slow.compute(make_landmarks(0.0, 0.0), 0.0)
        boosted.compute(make_landmarks(0.0, 0.0), 0.0)

        slow_dx, _ = slow.compute(make_landmarks(0.4, 0.0), 1.0)
        boosted_dx, _ = boosted.compute(make_landmarks(0.4, 0.0), 1.0)

        self.assertGreater(abs(boosted_dx), abs(slow_dx))


if __name__ == "__main__":
    unittest.main()
