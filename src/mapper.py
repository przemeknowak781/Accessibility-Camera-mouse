class CoordinateMapper:
    def __init__(self, cam_size, screen_size, frame_margin=100, screen_origin=(0, 0)):
        self.cam_w, self.cam_h = cam_size
        self.screen_w, self.screen_h = screen_size
        self.frame_margin = frame_margin
        self.origin_x, self.origin_y = screen_origin

    def map(self, x_cam, y_cam):
        x_clamped = min(max(x_cam, self.frame_margin), self.cam_w - self.frame_margin)
        y_clamped = min(max(y_cam, self.frame_margin), self.cam_h - self.frame_margin)

        x_norm = (x_clamped - self.frame_margin) / (self.cam_w - 2 * self.frame_margin)
        y_norm = (y_clamped - self.frame_margin) / (self.cam_h - 2 * self.frame_margin)

        x_screen = x_norm * self.screen_w + self.origin_x
        y_screen = y_norm * self.screen_h + self.origin_y
        return x_screen, y_screen
