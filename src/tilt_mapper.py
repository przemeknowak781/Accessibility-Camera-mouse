class TiltMapper:
    def __init__(self, decay=0.005, min_range=0.15):
        self.decay = float(decay)
        self.min_range = float(min_range)
        self.min_x = None
        self.max_x = None
        self.min_y = None
        self.max_y = None

    def reset(self):
        self.min_x = None
        self.max_x = None
        self.min_y = None
        self.max_y = None

    def update(self, tilt_x, tilt_y):
        if self.min_x is None:
            self.min_x = tilt_x
            self.max_x = tilt_x
            self.min_y = tilt_y
            self.max_y = tilt_y
        else:
            if tilt_x < self.min_x:
                self.min_x = tilt_x
            else:
                self.min_x += (tilt_x - self.min_x) * self.decay

            if tilt_x > self.max_x:
                self.max_x = tilt_x
            else:
                self.max_x += (tilt_x - self.max_x) * self.decay

            if tilt_y < self.min_y:
                self.min_y = tilt_y
            else:
                self.min_y += (tilt_y - self.min_y) * self.decay

            if tilt_y > self.max_y:
                self.max_y = tilt_y
            else:
                self.max_y += (tilt_y - self.max_y) * self.decay

        nx = self._normalize(tilt_x, self.min_x, self.max_x)
        ny = self._normalize(tilt_y, self.min_y, self.max_y)
        return nx, ny

    def _normalize(self, value, min_v, max_v):
        span = max(max_v - min_v, self.min_range)
        return (value - (min_v + max_v) * 0.5) / span + 0.5
