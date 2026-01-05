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


if __name__ == "__main__":
    unittest.main()
