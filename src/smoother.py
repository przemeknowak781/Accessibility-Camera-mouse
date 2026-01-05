class MotionSmoother:
    def __init__(
        self,
        max_speed=2600.0,
        damping=0.35,
        precision_radius=None,
        precision_damping=None,
        micro_radius=None,
        micro_damping=None,
    ):
        self.max_speed = float(max_speed)
        self.damping = float(damping)
        self.precision_radius = precision_radius
        self.precision_damping = precision_damping
        self.micro_radius = micro_radius
        self.micro_damping = micro_damping
        self._x = None
        self._y = None
        self._last_time = None

    def reset(self):
        self._x = None
        self._y = None
        self._last_time = None

    def apply(self, x, y, timestamp, precision=False):
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

        damping = self.damping
        if precision:
            if (
                self.micro_radius is not None
                and self.micro_damping is not None
                and step <= self.micro_radius
            ):
                damping = self.micro_damping
            elif (
                self.precision_radius is not None
                and self.precision_damping is not None
                and step <= self.precision_radius
            ):
                if (
                    self.micro_radius is not None
                    and self.micro_damping is not None
                    and self.micro_radius < self.precision_radius
                ):
                    t = (step - self.micro_radius) / (
                        self.precision_radius - self.micro_radius
                    )
                    t = max(0.0, min(1.0, t))
                    damping = self.micro_damping + (self.precision_damping - self.micro_damping) * t
                else:
                    damping = self.precision_damping

        self._x += dx * damping
        self._y += dy * damping
        return self._x, self._y
