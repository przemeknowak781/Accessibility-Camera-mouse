"""
SmartSnapper - UI element detection for cursor snapping.
Uses pywinauto to find interactive elements under/near the cursor.
"""
import threading
import time
import math

try:
    from pywinauto import Desktop
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False

from src.config import Config


class SmartSnapper(threading.Thread):
    def __init__(self, overlay=None):
        super().__init__(daemon=True)
        self._lock = threading.Lock()
        self._cursor_pos = None
        self._current_target = None
        self._detected_elements = []  # All elements for overlay
        self._active = False
        self._running = True
        self.available = HAS_PYWINAUTO
        self._overlay = overlay
        
        # Sticky target - once locked, don't change easily
        self._sticky_target = None
        self._sticky_rect = None
        
        # Interactive control types (pywinauto names)
        self._interactive = {
            "Button", "Hyperlink", "MenuItem", "TreeItem", "HeaderItem",
            "Edit", "CheckBox", "RadioButton", "ToggleButton", "SplitButton",
            "ComboBox", "ListItem", "TabItem", "Slider", "Spinner", 
            "ScrollBar", "Thumb", "DataItem", "Link",
        }
        # Ignored types - too generic
        self._ignore = {"Pane", "Window", "Document", "Group", "TitleBar", "Unknown", "Custom"}

    def set_overlay(self, overlay):
        """Set overlay for visualization."""
        self._overlay = overlay

    def set_active(self, active):
        with self._lock:
            self._active = bool(active)
            if not self._active:
                self._current_target = None
                self._sticky_target = None
                self._sticky_rect = None
                self._detected_elements = []

    def update_cursor_pos(self, x, y):
        with self._lock:
            self._cursor_pos = (int(x), int(y))

    def get_target(self):
        with self._lock:
            return self._current_target
    
    def get_detected_elements(self):
        with self._lock:
            return list(self._detected_elements)

    def stop(self):
        self._running = False

    def _is_interactive(self, wrapper):
        """Check if element is interactive."""
        try:
            ctype = wrapper.friendly_class_name()
            if ctype in self._ignore:
                return False
            if ctype in self._interactive:
                return True
            # Check for invoke pattern (clickable)
            try:
                if wrapper.is_invoke_pattern_available():
                    return True
            except:
                pass
            return False
        except:
            return False

    def _scan_nearby_elements(self, desktop, x, y, radius):
        """Scan for all interactive elements near cursor."""
        elements = []
        
        # Sample points in a grid around cursor
        step = 30  # Pixels between sample points
        points_checked = set()
        
        for dx in range(-int(radius), int(radius) + 1, step):
            for dy in range(-int(radius), int(radius) + 1, step):
                if dx*dx + dy*dy > radius*radius:
                    continue
                    
                px, py = x + dx, y + dy
                point_key = (px // 20, py // 20)  # Coarse grid to avoid duplicates
                if point_key in points_checked:
                    continue
                points_checked.add(point_key)
                
                try:
                    wrapper = desktop.from_point(px, py)
                    if not wrapper:
                        continue
                        
                    # Traverse up to find interactive element
                    curr = wrapper
                    for _ in range(5):
                        try:
                            if self._is_interactive(curr):
                                rect = curr.rectangle()
                                elem_key = (rect.left, rect.top, rect.right, rect.bottom)
                                # Avoid duplicates
                                if not any(e[:4] == (rect.left, rect.top, rect.width(), rect.height()) for e in elements):
                                    ctype = curr.friendly_class_name()
                                    elements.append((
                                        rect.left, rect.top, 
                                        rect.width(), rect.height(),
                                        ctype
                                    ))
                                break
                            parent = curr.parent()
                            if not parent:
                                break
                            curr = parent
                        except:
                            break
                except:
                    continue
        
        return elements

    def run(self):
        with open("snap_debug.txt", "w", encoding="utf-8") as f:
            f.write(f"SmartSnapper: Started. Available={self.available}\n")

        if not self.available:
            return

        desktop = Desktop(backend='uia')
        scan_counter = 0
        
        while self._running:
            try:
                with self._lock:
                    active = self._active
                    pos = self._cursor_pos
                    sticky = self._sticky_target
                    sticky_rect = self._sticky_rect
                
                if not active or pos is None:
                    # Clear overlay when inactive
                    if self._overlay:
                        self._overlay.set_elements([])
                        self._overlay.set_target(None)
                    time.sleep(Config.SNAP_INTERVAL)
                    continue

                x, y = pos
                target = None
                
                # Update overlay cursor position
                if self._overlay:
                    self._overlay.set_cursor((x, y))
                
                # STICKY LOGIC: Keep target if cursor is still near it
                if sticky is not None and sticky_rect is not None:
                    margin = 30  # Fixed margin in pixels
                    in_range = (sticky_rect[0] - margin <= x <= sticky_rect[2] + margin and
                               sticky_rect[1] - margin <= y <= sticky_rect[3] + margin)
                    
                    if in_range:
                        target = sticky
                    else:
                        with self._lock:
                            self._sticky_target = None
                            self._sticky_rect = None
                        sticky = None
                
                # Scan for elements periodically (every 5 cycles to save CPU)
                scan_counter += 1
                if scan_counter >= 5:
                    scan_counter = 0
                    elements = self._scan_nearby_elements(desktop, x, y, Config.SNAP_RADIUS)
                    
                    with self._lock:
                        self._detected_elements = elements
                    
                    # Update overlay
                    if self._overlay:
                        self._overlay.set_elements(elements)
                
                # Find best target if we don't have a sticky one
                if target is None:
                    with self._lock:
                        elements = list(self._detected_elements)
                    
                    best_dist = float('inf')
                    best_elem = None
                    
                    for elem in elements:
                        ex, ey, ew, eh, label = elem
                        cx = ex + ew / 2
                        cy = ey + eh / 2
                        dist = math.hypot(cx - x, cy - y)
                        
                        if dist < best_dist and dist <= Config.SNAP_RADIUS:
                            best_dist = dist
                            best_elem = (cx, cy, ex, ey, ex + ew, ey + eh, label)
                    
                    if best_elem:
                        cx, cy, left, top, right, bottom, label = best_elem
                        target = (float(cx), float(cy))
                        
                        with self._lock:
                            self._sticky_target = target
                            self._sticky_rect = (left, top, right, bottom)
                        
                        with open("snap_debug.txt", "a", encoding="utf-8") as f:
                            f.write(f"Target: {label} at {cx:.0f},{cy:.0f} (dist: {best_dist:.0f})\n")

                with self._lock:
                    self._current_target = target
                
                # Update overlay target
                if self._overlay:
                    self._overlay.set_target(target)

                time.sleep(Config.SNAP_INTERVAL)

            except Exception as e:
                with open("snap_debug.txt", "a", encoding="utf-8") as f:
                    f.write(f"Error: {e}\n")
                time.sleep(0.2)
