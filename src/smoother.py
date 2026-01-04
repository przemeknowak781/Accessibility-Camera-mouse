class MotionSmoother:
    def __init__(self, max_speed=2600.0, damping=0.35):
        self.max_speed = float(max_speed)
        self.damping = float(damping)
        self._x = None
        self._y = None
        self._last_time = None

    def reset(self):
        self._x = None
        self._y = None
        self._last_time = None

    def apply(self, x, y, timestamp):
        if self._x is None or self._y is None or self._last_time is None:
            self._x = float(x)
            self._y = float(y)
            self._last_time = float(timestamp)
            return self._x, self._y

        dt = max(float(timestamp) - self._last_time, 1e-6)
        self._last_time = float(timestamp)

        dx = x - self._x
        dy = y - self._y

        max_step = self.max_speed * dt
        step = (dx * dx + dy * dy) ** 0.5
        if step > max_step:
            scale = max_step / step
            dx *= scale
            dy *= scale

        self._x += dx * self.damping
        self._y += dy * self.damping
        return self._x, self._y
