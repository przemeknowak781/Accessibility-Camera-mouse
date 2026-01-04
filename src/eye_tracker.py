class EyeTracker:
    def __init__(self, smooth_alpha=0.35, gain=2.2, neutral_alpha=0.05):
        self.smooth_alpha = float(smooth_alpha)
        self.gain = float(gain)
        self.neutral_alpha = float(neutral_alpha)
        self._x = None
        self._y = None
        self._neutral = None
        self.calibrated = False
        self._calibration = {}
        self._map = None

        self._left = {
            "corner_l": 33,
            "corner_r": 133,
            "upper": 159,
            "lower": 145,
            "iris": [468, 469, 470, 471, 472],
        }
        self._right = {
            "corner_l": 362,
            "corner_r": 263,
            "upper": 386,
            "lower": 374,
            "iris": [473, 474, 475, 476, 477],
        }

    def reset(self):
        self._x = None
        self._y = None
        self._neutral = None
        self.calibrated = False
        self._calibration = {}
        self._map = None

    def start_calibration(self):
        self._calibration = {}
        self._map = None
        self.calibrated = False

    def add_calibration_sample(self, label, gaze):
        if gaze is None:
            return
        samples = self._calibration.setdefault(label, [])
        samples.append(gaze)

    def finish_calibration(self):
        required = ["BL", "BR", "TR", "TL"]
        if not all(label in self._calibration for label in required):
            return False

        def avg(label):
            pts = self._calibration[label]
            gx = sum(p[0] for p in pts) / len(pts)
            gy = sum(p[1] for p in pts) / len(pts)
            return gx, gy

        bl = avg("BL")
        br = avg("BR")
        tr = avg("TR")
        tl = avg("TL")

        x_min = (bl[0] + tl[0]) * 0.5
        x_max = (br[0] + tr[0]) * 0.5
        y_min = (tl[1] + tr[1]) * 0.5
        y_max = (bl[1] + br[1]) * 0.5

        if abs(x_max - x_min) < 1e-4 or abs(y_max - y_min) < 1e-4:
            return False

        self._map = (x_min, x_max, y_min, y_max)
        self.calibrated = True
        return True

    def map_to_screen(self, gaze):
        if not self._map or gaze is None:
            return gaze
        x_min, x_max, y_min, y_max = self._map
        gx = (gaze[0] - x_min) / (x_max - x_min)
        gy = (gaze[1] - y_min) / (y_max - y_min)
        gx = max(0.0, min(1.0, gx))
        gy = max(0.0, min(1.0, gy))
        return gx, gy

    def compute(self, landmarks):
        if not landmarks:
            return None

        left = self._eye_gaze(landmarks, self._left)
        right = self._eye_gaze(landmarks, self._right)

        if left is None and right is None:
            return None
        if left is None:
            gx, gy = right
        elif right is None:
            gx, gy = left
        else:
            gx = (left[0] + right[0]) * 0.5
            gy = (left[1] + right[1]) * 0.5

        gx = max(0.0, min(1.0, gx))
        gy = max(0.0, min(1.0, gy))

        if self._neutral is None:
            self._neutral = (gx, gy)
            self._x, self._y = 0.5, 0.5
            return self._x, self._y

        self._neutral = (
            self._neutral[0] * (1.0 - self.neutral_alpha) + gx * self.neutral_alpha,
            self._neutral[1] * (1.0 - self.neutral_alpha) + gy * self.neutral_alpha,
        )

        gx = 0.5 + (gx - self._neutral[0]) * self.gain
        gy = 0.5 + (gy - self._neutral[1]) * self.gain
        gx = max(0.0, min(1.0, gx))
        gy = max(0.0, min(1.0, gy))

        if self._x is None:
            self._x, self._y = gx, gy
        else:
            a = self.smooth_alpha
            self._x = self._x * (1.0 - a) + gx * a
            self._y = self._y * (1.0 - a) + gy * a
        return self._x, self._y

    def _eye_gaze(self, landmarks, idx):
        try:
            corner_l = landmarks[idx["corner_l"]]
            corner_r = landmarks[idx["corner_r"]]
            upper = landmarks[idx["upper"]]
            lower = landmarks[idx["lower"]]
        except Exception:
            return None

        iris_x = 0.0
        iris_y = 0.0
        count = 0
        for i in idx["iris"]:
            if i >= len(landmarks):
                continue
            lm = landmarks[i]
            iris_x += lm.x
            iris_y += lm.y
            count += 1
        if count == 0:
            return None

        iris_x /= count
        iris_y /= count

        span_x = max(corner_r.x - corner_l.x, 1e-6)
        span_y = max(lower.y - upper.y, 1e-6)

        gx = (iris_x - corner_l.x) / span_x
        gy = (iris_y - upper.y) / span_y
        return gx, gy
