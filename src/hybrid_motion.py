import math


class HybridMotion:
    def __init__(
        self,
        tilt_mapper,
        screen_size,
        screen_origin=(0, 0),
        fine_scale=0.18,
        fine_weight=1.0,
        coarse_weight=1.0,
    ):
        self.tilt_mapper = tilt_mapper
        self.screen_w, self.screen_h = screen_size
        self.origin_x, self.origin_y = screen_origin
        self.fine_scale = float(fine_scale)
        self.fine_weight = float(fine_weight)
        self.coarse_weight = float(coarse_weight)

    def reset(self):
        self.tilt_mapper.reset()

    def compute(self, landmarks, cam_size):
        cam_w, cam_h = cam_size
        wrist = None
        index_mcp = None
        pinky_mcp = None
        index_tip = None

        for idx, x, y, z in landmarks:
            if idx == 0:
                wrist = (x, y, z)
            elif idx == 5:
                index_mcp = (x, y, z)
            elif idx == 17:
                pinky_mcp = (x, y, z)
            elif idx == 8:
                index_tip = (x, y, z)

        if not (wrist and index_mcp and pinky_mcp and index_tip):
            return None

        vx1 = index_mcp[0] - wrist[0]
        vy1 = index_mcp[1] - wrist[1]
        vz1 = (index_mcp[2] - wrist[2]) * cam_w
        vx2 = pinky_mcp[0] - wrist[0]
        vy2 = pinky_mcp[1] - wrist[1]
        vz2 = (pinky_mcp[2] - wrist[2]) * cam_w

        nx = vy1 * vz2 - vz1 * vy2
        ny = vz1 * vx2 - vx1 * vz2
        nz = vx1 * vy2 - vy1 * vx2

        denom = abs(nz) + 1e-6
        tilt_x = nx / denom
        tilt_y = ny / denom

        coarse_x, coarse_y = self.tilt_mapper.update(tilt_x, tilt_y)
        x_coarse = self.origin_x + coarse_x * self.screen_w
        y_coarse = self.origin_y + coarse_y * self.screen_h

        hand_cx = (wrist[0] + index_mcp[0] + pinky_mcp[0]) / 3.0
        hand_cy = (wrist[1] + index_mcp[1] + pinky_mcp[1]) / 3.0
        span = math.hypot(index_mcp[0] - pinky_mcp[0], index_mcp[1] - pinky_mcp[1])
        span = max(span, 1.0)

        fine_dx = (index_tip[0] - hand_cx) / span
        fine_dy = (index_tip[1] - hand_cy) / span
        fine_dx = max(-1.0, min(1.0, fine_dx))
        fine_dy = max(-1.0, min(1.0, fine_dy))

        fine_px_x = fine_dx * self.fine_scale * self.screen_w * self.fine_weight
        fine_px_y = fine_dy * self.fine_scale * self.screen_h * self.fine_weight

        x_target = x_coarse * self.coarse_weight + fine_px_x
        y_target = y_coarse * self.coarse_weight + fine_px_y
        return x_target, y_target
