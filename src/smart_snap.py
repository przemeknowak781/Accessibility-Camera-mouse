import threading
import time

try:
    import uiautomation as auto
except Exception:
    auto = None

from src.config import Config


class SmartSnapper(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._lock = threading.Lock()
        self._cursor_pos = None
        self._current_target = None
        self._last_target = None
        self._active = False
        self._running = True
        self.available = auto is not None

        self._allowed_types = set()
        if auto is not None:
            control_names = [
                "ButtonControl",
                "HyperlinkControl",
                "MenuItemControl",
                "EditControl",
                "ListItemControl",
                "TabItemControl",
                "CheckBoxControl",
                "RadioButtonControl",
                "ComboBoxControl",
                "SliderControl",
                "SplitButtonControl",
                "ToggleButtonControl",
                "TreeItemControl",
                "SpinnerControl",
            ]
            for name in control_names:
                control = getattr(auto.ControlType, name, None)
                if control is not None:
                    self._allowed_types.add(control)
        self._allowed_names = {
            "Button",
            "ButtonControl",
            "Hyperlink",
            "HyperlinkControl",
            "MenuItem",
            "MenuItemControl",
            "Edit",
            "EditControl",
            "ListItem",
            "ListItemControl",
            "TabItem",
            "TabItemControl",
            "CheckBox",
            "CheckBoxControl",
            "RadioButton",
            "RadioButtonControl",
            "ComboBox",
            "ComboBoxControl",
            "Slider",
            "SliderControl",
            "SplitButton",
            "SplitButtonControl",
            "ToggleButton",
            "ToggleButtonControl",
            "TreeItem",
            "TreeItemControl",
            "Spinner",
            "SpinnerControl",
        }
        self._container_names = {
            "Pane",
            "PaneControl",
            "Window",
            "WindowControl",
            "Document",
            "DocumentControl",
            "Group",
            "GroupControl",
            "Custom",
            "CustomControl",
        }

    def set_active(self, active):
        with self._lock:
            self._active = bool(active)
            if not self._active:
                self._current_target = None
                self._last_target = None

    def update_cursor_pos(self, x, y):
        with self._lock:
            self._cursor_pos = (int(x), int(y))

    def get_target(self):
        with self._lock:
            return self._current_target

    def stop(self):
        self._running = False

    @staticmethod
    def _distance_to_rect(rect, x, y):
        if not rect:
            return None
        cx = min(max(x, rect.left), rect.right)
        cy = min(max(y, rect.top), rect.bottom)
        dx = cx - x
        dy = cy - y
        return (dx * dx + dy * dy) ** 0.5

    @staticmethod
    def _distance_to_point(x, y, cx, cy):
        dx = cx - x
        dy = cy - y
        return (dx * dx + dy * dy) ** 0.5

    @staticmethod
    def _clickable_point(element):
        try:
            point = element.GetClickablePoint()
            if point:
                return float(point.x), float(point.y)
        except Exception:
            return None
        return None

    def _is_allowed_element(self, element):
        if element is None:
            return False
        control_type = getattr(element, "ControlType", None)
        if control_type in self._allowed_types:
            return True
        name = getattr(element, "ControlTypeName", None)
        if name in self._allowed_names:
            return True
        if self._clickable_point(element):
            return True
        return False

    def _target_from_element(self, element, x, y, snap_radius):
        clickable = self._clickable_point(element)
        if clickable:
            cx, cy = clickable
            dist = self._distance_to_point(x, y, cx, cy)
        else:
            rect = getattr(element, "BoundingRectangle", None)
            if rect:
                cx = (rect.left + rect.right) * 0.5
                cy = (rect.top + rect.bottom) * 0.5
                dist = self._distance_to_rect(rect, x, y)
            else:
                return None
        if dist is None or dist > snap_radius:
            return None
        return (float(cx), float(cy))

    def _pick_target(self, element, x, y, snap_radius):
        ctrl = element
        for _ in range(4):
            if ctrl is None:
                break
            if self._is_allowed_element(ctrl):
                target = self._target_from_element(ctrl, x, y, snap_radius)
                if target is not None:
                    return target
            try:
                ctrl = ctrl.GetParentControl()
            except Exception:
                break

        if element is None:
            return None
        try:
            stack = list(element.GetChildren() or [])
        except Exception:
            return None

        best_target = None
        best_dist = None
        visited = 0
        while stack and visited < 80:
            child = stack.pop(0)
            visited += 1
            if self._is_allowed_element(child):
                target = self._target_from_element(child, x, y, snap_radius)
                if target is not None:
                    dist = self._distance_to_point(x, y, target[0], target[1])
                    if best_dist is None or dist < best_dist:
                        best_target = target
                        best_dist = dist
            ctype = getattr(child, "ControlTypeName", None)
            if ctype in self._container_names:
                try:
                    kids = child.GetChildren() or []
                except Exception:
                    kids = []
                if kids:
                    stack.extend(kids[:10])
        return best_target

    def run(self):
        if not self.available:
            return

        init = getattr(auto, "InitializeUIAutomationInThread", None)
        uninit = getattr(auto, "UninitializeUIAutomationInThread", None)
        if init:
            init()
        try:
            while self._running:
                with self._lock:
                    active = self._active
                    pos = self._cursor_pos
                if not active or pos is None:
                    time.sleep(Config.SNAP_INTERVAL)
                    continue
                x, y = pos
                target = None
                try:
                    if hasattr(auto, "ControlFromPoint"):
                        element = auto.ControlFromPoint(int(x), int(y))
                    else:
                        element = auto.ControlFromPoint2(int(x), int(y))
                    candidate = self._pick_target(element, x, y, Config.SNAP_RADIUS)
                    if candidate is not None and self._last_target is not None:
                        cand_dist = self._distance_to_point(x, y, candidate[0], candidate[1])
                        prev_dist = self._distance_to_point(
                            x, y, self._last_target[0], self._last_target[1]
                        )
                        sticky_margin = max(6.0, Config.SNAP_RADIUS * 0.15)
                        if prev_dist <= Config.SNAP_RADIUS and prev_dist <= cand_dist + sticky_margin:
                            target = self._last_target
                        else:
                            target = candidate
                    else:
                        target = candidate
                except Exception:
                    target = None

                with self._lock:
                    self._current_target = target
                    if target is not None:
                        self._last_target = target

                time.sleep(Config.SNAP_INTERVAL)
        finally:
            if uninit:
                uninit()
