import cv2
import numpy as np


from src.config import Config

class HudRenderer:
    def __init__(self, frame_size):
        self.w, self.h = frame_size
        self.accent = Config.COLOR_ACCENT
        self.accent_2 = Config.COLOR_ACCENT_2
        self.dark = Config.COLOR_DARK
        self.light = Config.COLOR_LIGHT

    def _blend_panel(self, frame, rect, color, alpha=0.75):
        x1, y1, x2, y2 = rect
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def draw_hud(
        self,
        frame,
        fps,
        click_active,
        coords,
        events=None,
        probs=None,
        paused=False,
        mode_label=None,
        tune=None,
        gaze=None,
        calibration=None,
    ):
        panel_h = 56
        self._blend_panel(frame, (16, 16, self.w - 16, 16 + panel_h), self.dark, 0.75)

        cv2.putText(
            frame,
            'Handsteer',
            (30, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            self.light,
            2,
            cv2.LINE_AA,
        )
        
        cv2.putText(
            frame,
            f'FPS {fps:.1f}',
            (160, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.accent,
            2,
            cv2.LINE_AA,
        )

        status_text = 'CLICK' if click_active else 'READY'
        status_color = self.accent_2 if click_active else self.accent
        cv2.circle(frame, (self.w - 120, 44), 10, status_color, -1)
        cv2.putText(
            frame,
            status_text,
            (self.w - 100, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.light,
            2,
            cv2.LINE_AA,
        )

        if coords is not None:
            x, y = coords
            cv2.putText(
                frame,
                f'{int(x):04d},{int(y):04d}',
                (self.w - 240, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                self.light,
                1,
                cv2.LINE_AA,
            )

        if mode_label:
            self._draw_mode_badge(frame, mode_label)
        if tune:
            self._draw_tuning(frame, tune)

        if probs:
            self._draw_probs(frame, probs)
        if events:
            self._draw_events(frame, events)

        if paused:
            self._draw_paused(frame)

        if gaze:
            self._draw_gaze_dot(frame, gaze)
        if calibration:
            self._draw_calibration(frame, calibration)

        self._draw_corner_glow(frame)

    def _draw_probs(self, frame, probs):
        panel_w = 220
        panel_h = 86
        x1, y1 = 16, 86
        x2, y2 = x1 + panel_w, y1 + panel_h
        self._blend_panel(frame, (x1, y1, x2, y2), self.dark, 0.7)

        cv2.putText(
            frame,
            "Signals",
            (x1 + 10, y1 + 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.light,
            1,
            cv2.LINE_AA,
        )

        items = [("Blink", probs.get("blink")), ("Pinch", probs.get("pinch"))]
        y = y1 + 46
        for label, value in items:
            if value is None:
                text = f"{label}: --"
            else:
                text = f"{label}: {value:0.2f}"
            cv2.putText(
                frame,
                text,
                (x1 + 10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                self.accent,
                1,
                cv2.LINE_AA,
            )
            y += 18

    def _draw_events(self, frame, events):
        panel_w = 300
        panel_h = 130
        x1, y1 = 16, self.h - panel_h - 16
        x2, y2 = x1 + panel_w, y1 + panel_h
        self._blend_panel(frame, (x1, y1, x2, y2), self.dark, 0.72)

        cv2.putText(
            frame,
            "Events",
            (x1 + 10, y1 + 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.light,
            1,
            cv2.LINE_AA,
        )

        y = y1 + 46
        for line in events[:5]:
            cv2.putText(
                frame,
                line,
                (x1 + 10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                self.light,
                1,
                cv2.LINE_AA,
            )
            y += 16

    def _draw_tuning(self, frame, tune):
        panel_w = 380
        panel_h = 46 + max(len(tune), 1) * 22
        x1, y1 = self.w - panel_w - 16, 86
        x2, y2 = x1 + panel_w, y1 + panel_h
        self._blend_panel(frame, (x1, y1, x2, y2), self.dark, 0.7)

        cv2.putText(
            frame,
            "Quick Controls",
            (x1 + 12, y1 + 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            self.light,
            1,
            cv2.LINE_AA,
        )

        cv2.line(frame, (x1 + 10, y1 + 36), (x2 - 10, y1 + 36), self.accent, 1)

        y = y1 + 60
        for item in tune:
            label = item[0]
            value = item[1]
            keys = item[2] if len(item) > 2 else []
            cv2.putText(
                frame,
                f"{label}",
                (x1 + 10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                self.light,
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"{value}",
                (x1 + 120, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                self.accent,
                1,
                cv2.LINE_AA,
            )
            if keys:
                self._draw_keycaps(frame, keys, x2 - 12, y - 12)
            y += 22

    def _draw_mode_badge(self, frame, mode_label):
        text = f"MODE {mode_label}"
        x1, y1, x2, y2 = self.w - 280, 16, self.w - 16, 56
        self._blend_panel(frame, (x1, y1, x2, y2), self.dark, 0.8)
        cv2.putText(
            frame,
            text,
            (x1 + 16, y2 - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            self.accent,
            2,
            cv2.LINE_AA,
        )

    def _draw_paused(self, frame):
        cv2.putText(
            frame,
            'PAUSED',
            (self.w - 140, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        center_x, center_y = self.w // 2, self.h // 2
        cv2.putText(
            frame,
            "PAUSED",
            (center_x - 80, center_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 0, 255),
            2,
        )
        cv2.putText(
            frame,
            "Press SPACE to Resume",
            (center_x - 140, center_y + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.light,
            1,
        )

    def _draw_gaze_dot(self, frame, gaze):
        gx, gy = gaze
        x = int(max(0, min(self.w - 1, gx * self.w)))
        y = int(max(0, min(self.h - 1, gy * self.h)))
        cv2.circle(frame, (x, y), 8, (0, 0, 0), -1)
        cv2.circle(frame, (x, y), 6, self.accent, -1)
        cv2.circle(frame, (x, y), 12, self.accent_2, 1)

    def _draw_calibration(self, frame, calibration):
        name, target, step, total = calibration
        tx = int(target[0] * self.w)
        ty = int(target[1] * self.h)

        cv2.circle(frame, (tx, ty), 16, (0, 0, 0), -1)
        cv2.circle(frame, (tx, ty), 12, self.accent, -1)
        cv2.circle(frame, (tx, ty), 24, self.accent_2, 2)

        text = f"Look at {name} and press ENTER ({step}/{total})"
        cv2.putText(
            frame,
            text,
            (20, self.h - 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.light,
            2,
            cv2.LINE_AA,
        )

    def _draw_keycaps(self, frame, keys, right_x, baseline_y):
        pad = 6
        gap = 6
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        thickness = 1

        x = right_x
        for key in reversed(keys):
            (w, h), _ = cv2.getTextSize(key, font, scale, thickness)
            box_w = w + pad * 2
            box_h = h + pad
            x1 = x - box_w
            y1 = baseline_y - h - 2
            x2 = x
            y2 = y1 + box_h
            self._blend_panel(frame, (x1, y1, x2, y2), (40, 46, 60), 0.85)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (90, 100, 120), 1)
            cv2.putText(
                frame,
                key,
                (x1 + pad, y2 - pad),
                font,
                scale,
                self.light,
                thickness,
                cv2.LINE_AA,
            )
            x = x1 - gap

    def _draw_corner_glow(self, frame):
        glow = np.zeros_like(frame, dtype=np.uint8)
        cv2.circle(glow, (60, self.h - 40), 120, (50, 110, 255), -1)
        cv2.circle(glow, (self.w - 60, self.h - 40), 120, (80, 255, 160), -1)
        cv2.addWeighted(glow, 0.12, frame, 0.88, 0, frame)
