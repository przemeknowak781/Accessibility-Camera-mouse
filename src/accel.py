import math


class MotionAccelerator:
    def __init__(self, min_speed=200.0, max_speed=1800.0, max_gain=2.2, exp=1.4):
        self.min_speed = float(min_speed)
        self.max_speed = float(max_speed)
        self.max_gain = float(max_gain)
        self.exp = float(exp)
        self._last_raw_x = None
        self._last_raw_y = None
        self._last_time = None

    def reset(self):
        self._last_raw_x = None
        self._last_raw_y = None
        self._last_time = None

    def apply(self, x, y, timestamp):
        if self._last_raw_x is None or self._last_raw_y is None or self._last_time is None:
            self._last_raw_x = float(x)
            self._last_raw_y = float(y)
            self._last_time = float(timestamp)
            return float(x), float(y)

        dt = max(float(timestamp) - self._last_time, 1e-6)
        self._last_time = float(timestamp)

        dx = float(x) - self._last_raw_x
        dy = float(y) - self._last_raw_y
        speed = math.hypot(dx, dy) / dt

        if self.max_speed <= self.min_speed:
            gain = 1.0
        else:
            t = (speed - self.min_speed) / (self.max_speed - self.min_speed)
            t = max(0.0, min(1.0, t))
            t = t ** self.exp
            gain = 1.0 + t * (self.max_gain - 1.0)

        x_out = float(x) + dx * (gain - 1.0)
        y_out = float(y) + dy * (gain - 1.0)

        self._last_raw_x = float(x)
        self._last_raw_y = float(y)
        return x_out, y_out
