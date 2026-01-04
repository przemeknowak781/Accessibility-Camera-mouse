import math


class LowPassFilter:
    def __init__(self, alpha, init_value=0.0):
        self.alpha = alpha
        self.initialized = False
        self.y = init_value

    def apply(self, value, alpha=None):
        if alpha is None:
            alpha = self.alpha
        if not self.initialized:
            self.y = value
            self.initialized = True
            return value
        self.y = alpha * value + (1.0 - alpha) * self.y
        return self.y


class OneEuroFilter:
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_filter = LowPassFilter(1.0)
        self.dx_filter = LowPassFilter(1.0)
        self.last_time = None

    def _alpha(self, cutoff, dt):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, value, timestamp):
        if self.last_time is None:
            self.last_time = timestamp
            self.x_filter.initialized = False
            self.dx_filter.initialized = False
            return value

        dt = max(timestamp - self.last_time, 1e-6)
        self.last_time = timestamp

        dx = (value - self.x_filter.y) / dt if self.x_filter.initialized else 0.0
        alpha_d = self._alpha(self.d_cutoff, dt)
        edx = self.dx_filter.apply(dx, alpha_d)

        cutoff = self.min_cutoff + self.beta * abs(edx)
        alpha = self._alpha(cutoff, dt)
        return self.x_filter.apply(value, alpha)
