import time

from src.config import Config
from src.smart_snap import SmartSnapper


class SnapController:
    def __init__(self, mouse_driver, event_log, snapper=None, overlay=None):
        self.mouse_driver = mouse_driver
        self.event_log = event_log
        self.enabled = Config.SNAP_ENABLED
        self.active = False
        self._active_until = 0.0
        self._overlay = overlay
        self._snapper = snapper or SmartSnapper(overlay=overlay)
        self._filtered_target = None
        self._target_hold_until = 0.0
        self._last_logged = None
        self._last_empty_log = 0.0
        if getattr(self._snapper, "available", False):
            self._snapper.start()
            self.event_log.add("SNAP_AVAILABLE")
        else:
            self.enabled = False
            self.event_log.add("SNAP_UNAVAILABLE")

    def stop(self):
        self._snapper.stop()

    def toggle_enabled(self):
        if not self._snapper.available:
            self.enabled = False
            self.event_log.add("SNAP_UNAVAILABLE")
            return False
        self.enabled = not self.enabled
        if not self.enabled:
            self._snapper.set_active(False)
            self.mouse_driver.set_snap_target(None)
        state = "ON" if self.enabled else "OFF"
        self.event_log.add(f"SNAP_{state}")
        return self.enabled

    def update_active(self, brows_raised, timestamp):
        now = float(timestamp)
        if brows_raised:
            self._active_until = now + Config.SNAP_BROW_HOLD_SECONDS
        if Config.SNAP_TRIGGER_MODE == "ALWAYS":
            active = self.enabled
        else:
            active = self.enabled and now <= self._active_until
        self.active = active
        self._snapper.set_active(active)
        if not active:
            self._filtered_target = None
            self._target_hold_until = 0.0

    def update_cursor_pos(self, x, y):
        if self.enabled:
            self._snapper.update_cursor_pos(x, y)
            self._last_cursor_pos = (x, y)

    def sync_target(self):
        now = time.time()
        target = self._snapper.get_target() if self.active else None
        
        if self.active and target is None and now - self._last_empty_log >= 1.5:
            self.event_log.add("SNAP_EMPTY")
            self._last_empty_log = now
            
        # Simple hold: keep last target for a short time if new one is None
        if target is None:
            if now <= self._target_hold_until:
                target = self._filtered_target
            else:
                self._filtered_target = None
        else:
            self._target_hold_until = now + Config.SNAP_TARGET_HOLD_SECONDS
            # Basic smoothing: interpolate towards new target
            if self._filtered_target is None:
                self._filtered_target = target
            else:
                alpha = Config.SNAP_TARGET_SMOOTH
                fx = self._filtered_target[0] + (target[0] - self._filtered_target[0]) * alpha
                fy = self._filtered_target[1] + (target[1] - self._filtered_target[1]) * alpha
                self._filtered_target = (fx, fy)
            target = self._filtered_target

        # Logging
        if target is None and self._last_logged is not None:
            self.event_log.add("SNAP_LOST")
            self._last_logged = None
        elif target is not None and self._last_logged is None:
            self.event_log.add("SNAP_TARGET")
            self._last_logged = target

        self.mouse_driver.set_snap_target(target)
        return target

    def debug_probe(self):
        try:
            import uiautomation as auto
        except Exception:
            self.event_log.add("SNAP_DEBUG_NO_UIA")
            return
        try:
            pos = auto.GetCursorPos()
            if hasattr(auto, "ControlFromPoint2"):
                elem = auto.ControlFromPoint2(pos[0], pos[1])
            else:
                elem = auto.ControlFromPoint(pos[0], pos[1])
            if not elem:
                self.event_log.add("SNAP_DEBUG_NONE")
                return
            ctype = getattr(elem, "ControlTypeName", "unknown")
            name = getattr(elem, "Name", "") or "unnamed"
            rect = getattr(elem, "BoundingRectangle", None)
            if rect:
                info = f"{ctype}:{name}:{rect.left},{rect.top},{rect.right},{rect.bottom}"
            else:
                info = f"{ctype}:{name}:norect"
            self.event_log.add(f"SNAP_DEBUG {info}")
        except Exception:
            self.event_log.add("SNAP_DEBUG_ERROR")
