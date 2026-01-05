import unittest

from src.mouse_driver import MouseDriver


class FakeController:
    def __init__(self, pos=(0.0, 0.0)):
        self.position = pos
        self.moves = []

    def get_position(self):
        return self.position

    def move(self, x, y):
        self.position = (x, y)
        self.moves.append((x, y))


class MouseDriverTests(unittest.TestCase):
    def test_active_tracking_moves_toward_target(self):
        controller = FakeController()
        driver = MouseDriver(controller)
        driver.speed_coeff = 1.0
        driver.friction = 0.5
        driver.coast_window = 0.5

        driver.update_target(0.0, 0.0, timestamp=0.0)
        driver.update_target(10.0, 0.0, timestamp=0.0)
        driver.step(0.0, *controller.get_position(), 0.1)

        self.assertAlmostEqual(controller.position[0], 1.0, places=3)
        self.assertAlmostEqual(controller.position[1], 0.0, places=3)

    def test_coast_applies_friction(self):
        controller = FakeController()
        driver = MouseDriver(controller)
        driver.speed_coeff = 1.0
        driver.friction = 0.5
        driver.coast_window = 0.5

        driver.update_target(0.0, 0.0, timestamp=0.0)
        driver.update_target(10.0, 0.0, timestamp=0.0)
        driver.step(0.0, *controller.get_position(), 0.1)
        driver.step(0.2, *controller.get_position(), 0.1)

        self.assertAlmostEqual(controller.position[0], 1.5, places=3)
        self.assertAlmostEqual(controller.position[1], 0.0, places=3)

    def test_snap_applies_when_slow(self):
        from src import config

        config.Config.SNAP_ENABLED = True
        config.Config.SNAP_RADIUS = 100.0
        config.Config.SNAP_STRENGTH = 0.5
        config.Config.SNAP_LOCK_RADIUS = 10.0
        config.Config.SNAP_LOCK_STRENGTH = 0.9
        config.Config.SNAP_BREAKOUT_SPEED = 50.0

        controller = FakeController()
        driver = MouseDriver(controller)
        target_x, target_y = driver._apply_snap(
            10.0, 0.0, 0.0, 0.0, (50.0, 0.0), speed=0.0
        )
        self.assertAlmostEqual(target_x, 40.6667, places=3)
        self.assertAlmostEqual(target_y, 0.0, places=3)

    def test_snap_ignored_when_fast(self):
        from src import config

        config.Config.SNAP_ENABLED = True
        config.Config.SNAP_RADIUS = 100.0
        config.Config.SNAP_STRENGTH = 0.5
        config.Config.SNAP_LOCK_RADIUS = 10.0
        config.Config.SNAP_LOCK_STRENGTH = 0.9
        config.Config.SNAP_BREAKOUT_SPEED = 10.0

        controller = FakeController()
        driver = MouseDriver(controller)
        target_x, target_y = driver._apply_snap(
            10.0, 0.0, 0.0, 0.0, (50.0, 0.0), speed=20.0
        )
        self.assertAlmostEqual(target_x, 10.0, places=3)
        self.assertAlmostEqual(target_y, 0.0, places=3)

    def test_snap_locks_when_close(self):
        from src import config

        config.Config.SNAP_ENABLED = True
        config.Config.SNAP_RADIUS = 100.0
        config.Config.SNAP_STRENGTH = 0.5
        config.Config.SNAP_LOCK_RADIUS = 10.0
        config.Config.SNAP_LOCK_STRENGTH = 0.9
        config.Config.SNAP_BREAKOUT_SPEED = 50.0

        controller = FakeController(pos=(45.0, 0.0))
        driver = MouseDriver(controller)
        driver.set_snap_target((50.0, 0.0))
        driver.update_target(45.0, 0.0, timestamp=0.0)
        driver.step(0.1, *controller.get_position(), 0.1)
        self.assertAlmostEqual(controller.position[0], 50.0, places=3)
        self.assertAlmostEqual(controller.position[1], 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
