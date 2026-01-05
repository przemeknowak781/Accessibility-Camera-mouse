class BlinkStateMachine:
    def __init__(
        self,
        blink_threshold=0.22,
        blink_seconds=0.03,
        cooldown=0.4,
        long_blink_seconds=0.7,
    ):
        self.blink_threshold = float(blink_threshold)
        self.blink_seconds = max(float(blink_seconds), 0.0)
        self.cooldown = float(cooldown)
        self.long_blink_seconds = max(float(long_blink_seconds), 0.0)
        self._closed_time = 0.0
        self._ready = True
        self._last_blink_time = 0.0
        self._last_timestamp = None
        self._long_sent = False

    def reset(self):
        self._closed_time = 0.0
        self._ready = True
        self._last_blink_time = 0.0
        self._last_timestamp = None
        self._long_sent = False

    def update(self, left_ratio, right_ratio, timestamp):
        left_closed = left_ratio < self.blink_threshold
        right_closed = right_ratio < self.blink_threshold

        state = None
        if left_closed and right_closed:
            state = "BOTH"
        elif left_closed:
            state = "LEFT"
        elif right_closed:
            state = "RIGHT"

        dt = 0.0
        if self._last_timestamp is not None:
            dt = max(float(timestamp) - float(self._last_timestamp), 0.0)
        self._last_timestamp = float(timestamp)

        blink_detected = None
        long_blink = False

        if state:
            self._closed_time += dt
            if self._ready and self._closed_time >= self.blink_seconds:
                if (timestamp - self._last_blink_time) > self.cooldown:
                    self._last_blink_time = timestamp
                    self._ready = False
                    blink_detected = state
            if (
                self.long_blink_seconds > 0.0
                and state == "BOTH"
                and not self._long_sent
                and self._closed_time >= self.long_blink_seconds
            ):
                self._long_sent = True
                long_blink = True
        else:
            if (
                left_ratio > self.blink_threshold * 1.1
                and right_ratio > self.blink_threshold * 1.1
            ):
                self._closed_time = 0.0
                self._ready = True
                self._long_sent = False

        return blink_detected, long_blink
