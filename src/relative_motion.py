class RelativeMotion:
    def __init__(self, cam_size, screen_size, sensitivity=2.0):
        self.cam_w, self.cam_h = cam_size
        self.screen_w, self.screen_h = screen_size
        self.sensitivity = float(sensitivity)
        self._prev_hand = None

    def reset(self):
        self._prev_hand = None

    def update(self, hand_pos):
        if hand_pos is None:
            self._prev_hand = None
            return None

        x, y = hand_pos
        if self._prev_hand is None:
            self._prev_hand = (float(x), float(y))
            return 0.0, 0.0

        dx_cam = float(x) - self._prev_hand[0]
        dy_cam = float(y) - self._prev_hand[1]
        self._prev_hand = (float(x), float(y))

        scale_x = self.screen_w / max(self.cam_w, 1.0)
        scale_y = self.screen_h / max(self.cam_h, 1.0)
        dx_screen = dx_cam * scale_x * self.sensitivity
        dy_screen = dy_cam * scale_y * self.sensitivity
        return dx_screen, dy_screen
