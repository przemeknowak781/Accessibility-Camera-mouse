import unittest

from src.camera_watchdog import is_camera_stalled


class CameraWatchdogTests(unittest.TestCase):
    def test_none_frame_time_not_stalled(self):
        self.assertFalse(is_camera_stalled(None, 10.0, 1.0))

    def test_stall_threshold(self):
        self.assertFalse(is_camera_stalled(1.0, 1.9, 1.0))
        self.assertTrue(is_camera_stalled(1.0, 2.0, 1.0))


if __name__ == "__main__":
    unittest.main()

