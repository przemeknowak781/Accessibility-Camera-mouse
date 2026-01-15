class HeadMotion:
    def __init__(
        self,
        screen_size,
        screen_origin=(0, 0),
        sensitivity=2.6,
        deadzone=0.02,
        min_speed=80.0,
        max_speed=2200.0,
        exp=0.7,
        neutral_alpha=0.08,
        micro_gain=1.8,
        stop_threshold=0.01,
        stop_hold=0.12,
        return_brake=0.6,
        return_brake_margin=0.01,
        tilt_boost=0.4,
    ):
        self.screen_w, self.screen_h = screen_size
        self.origin_x, self.origin_y = screen_origin
        self.sensitivity = float(sensitivity)
        self.deadzone = float(deadzone)
        self.min_speed = float(min_speed)
        self.max_speed = float(max_speed)
        self.exp = float(exp)
        self.neutral_alpha = float(neutral_alpha)
        self.micro_gain = float(micro_gain)
        self.stop_threshold = float(stop_threshold)
        self.stop_hold = float(stop_hold)
        self.return_brake = float(return_brake)
        self.return_brake_margin = float(return_brake_margin)
        self.tilt_boost = float(tilt_boost)
        self._neutral = None
        self._last_time = None
        self._below_since = None
        self._last_mag = None

    def reset(self):
        self._neutral = None
        self._last_time = None
        self._below_since = None
        self._last_mag = None

    def compute(self, landmarks, timestamp):
        if not landmarks:
            return None

        # Single pass to find min/max for both axes
        first = landmarks[0]
        min_x = max_x = first.x
        min_y = max_y = first.y
        for lm in landmarks[1:]:
            if lm.x < min_x:
                min_x = lm.x
            elif lm.x > max_x:
                max_x = lm.x
            if lm.y < min_y:
                min_y = lm.y
            elif lm.y > max_y:
                max_y = lm.y
        span_x = max(max_x - min_x, 1e-6)
        span_y = max(max_y - min_y, 1e-6)
        cx = (min_x + max_x) * 0.5
        cy = (min_y + max_y) * 0.5

        nose_idx = 1 if len(landmarks) > 1 else 0
        nose = landmarks[nose_idx]

        raw_dx = (nose.x - cx) / span_x
        raw_dy = (nose.y - cy) / span_y

        if self._neutral is None:
            self._neutral = (raw_dx, raw_dy)
            self._last_time = float(timestamp)
            return 0.0, 0.0

        dt = max(float(timestamp) - self._last_time, 1e-6)
        self._last_time = float(timestamp)

        # Slow adaptive neutral to reduce drift and reduce required head movement.
        self._neutral = (
            self._neutral[0] * (1.0 - self.neutral_alpha) + raw_dx * self.neutral_alpha,
            self._neutral[1] * (1.0 - self.neutral_alpha) + raw_dy * self.neutral_alpha,
        )

        dx = raw_dx - self._neutral[0]
        dy = raw_dy - self._neutral[1]

        dx = self._apply_deadzone(dx)
        dy = self._apply_deadzone(dy)

        dx *= self.sensitivity
        dy *= self.sensitivity

        mag = (dx * dx + dy * dy) ** 0.5
        if mag < self.stop_threshold:
            if self._below_since is None:
                self._below_since = float(timestamp)
            elif (timestamp - self._below_since) >= self.stop_hold:
                # Snap neutral to current pose to help stop/hold.
                self._neutral = (raw_dx, raw_dy)
                self._last_mag = 0.0
                return 0.0, 0.0
        else:
            self._below_since = None

        mag_total = mag
        vx = self._scale_speed(dx, abs(dx), mag_total)
        vy = self._scale_speed(dy, abs(dy), mag_total)
        if (
            self._last_mag is not None
            and mag + self.return_brake_margin < self._last_mag
            and self._last_mag > 0.0
        ):
            ratio = mag / self._last_mag
            brake = self.return_brake + (1.0 - self.return_brake) * ratio
            vx *= brake
            vy *= brake
        self._last_mag = mag
        return vx * dt, vy * dt

    def _apply_deadzone(self, value):
        if abs(value) <= self.deadzone:
            return 0.0
        sign = 1.0 if value > 0 else -1.0
        return sign * (abs(value) - self.deadzone)

    def _scale_speed(self, value, axis_mag, total_mag):
        if value == 0.0:
            return 0.0
        sign = 1.0 if value > 0 else -1.0
        axis_mag = min(abs(axis_mag), 1.0)
        if axis_mag < 0.2:
            axis_mag = axis_mag * self.micro_gain
        speed = self.min_speed + (self.max_speed - self.min_speed) * (axis_mag ** self.exp)
        total_mag = min(abs(total_mag), 1.0)
        speed *= 1.0 + self.tilt_boost * total_mag
        return sign * speed
