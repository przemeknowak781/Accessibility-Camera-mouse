import time
import unittest

from src.snap_controller import SnapController


class FakeSnapper:
    def __init__(self):
        self.available = True
        self._target = None
        self._active = False

    def start(self):
        return None

    def stop(self):
        return None

    def set_active(self, active):
        self._active = active

    def update_cursor_pos(self, x, y):
        return None

    def get_target(self):
        return self._target


class FakeDriver:
    def __init__(self):
        self.snap_target = None

    def set_snap_target(self, target):
        self.snap_target = target


class FakeLog:
    def add(self, _event, _timestamp=None):
        return None


class SnapControllerTests(unittest.TestCase):
    def test_filters_target_and_holds(self):
        snapper = FakeSnapper()
        driver = FakeDriver()
        controller = SnapController(driver, FakeLog(), snapper=snapper)
        controller.enabled = True
        controller.active = True

        snapper._target = (100.0, 100.0)
        target = controller.sync_target()
        self.assertEqual(target, (100.0, 100.0))

        snapper._target = None
        target = controller.sync_target()
        self.assertEqual(target, (100.0, 100.0))


if __name__ == "__main__":
    unittest.main()
