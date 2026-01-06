import unittest

from src import snap_controller as snap_controller_mod
from src.snap_controller import SnapController
from src.config import Config


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
    def test_hold_expires_without_interpolation(self):
        snapper = FakeSnapper()
        driver = FakeDriver()
        controller = SnapController(driver, FakeLog(), snapper=snapper)
        controller.enabled = True
        controller.active = True

        original_hold = Config.SNAP_TARGET_HOLD_SECONDS
        original_time = snap_controller_mod.time.time
        try:
            Config.SNAP_TARGET_HOLD_SECONDS = 0.2
            now = 1000.0
            snap_controller_mod.time.time = lambda: now

            snapper._target = (100.0, 100.0)
            target = controller.sync_target()
            self.assertEqual(target, (100.0, 100.0))

            snapper._target = None
            target = controller.sync_target()
            self.assertEqual(target, (100.0, 100.0))

            now += 0.25
            target = controller.sync_target()
            self.assertIsNone(target)
        finally:
            Config.SNAP_TARGET_HOLD_SECONDS = original_hold
            snap_controller_mod.time.time = original_time

    def test_switches_to_new_target_immediately(self):
        snapper = FakeSnapper()
        driver = FakeDriver()
        controller = SnapController(driver, FakeLog(), snapper=snapper)
        controller.enabled = True
        controller.active = True

        original_time = snap_controller_mod.time.time
        try:
            snap_controller_mod.time.time = lambda: 1000.0
            snapper._target = (100.0, 100.0)
            target = controller.sync_target()
            self.assertEqual(target, (100.0, 100.0))

            snapper._target = (240.0, 180.0)
            target = controller.sync_target()
            self.assertEqual(target, (240.0, 180.0))
        finally:
            snap_controller_mod.time.time = original_time


if __name__ == "__main__":
    unittest.main()
