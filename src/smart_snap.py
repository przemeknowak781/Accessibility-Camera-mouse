"""
SmartSnapper - UI element detection for cursor snapping.
Uses pywinauto to find interactive elements under the cursor.
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
        self._active = False
        self._running = True
        self.available = HAS_PYWINAUTO
        self._overlay = overlay  # Not used when overlay is None
        
        # Interactive control types (pywinauto friendly names)
        self._interactive = {
            "Button", "Hyperlink", "MenuItem", "TreeItem", "HeaderItem",
            "Edit", "CheckBox", "RadioButton", "ToggleButton", "SplitButton",
            "ComboBox", "ListItem", "TabItem", "Slider", "Spinner", 
            "ScrollBar", "Thumb", "DataItem", "Link", "Image", "Tab",
            "List", "Header", "ToolBar", "ToolItem", "Pane", "Group"
        }
        # Only ignore these top-level containers
        self._ignore = {"Window", "Document", "TitleBar"}

    def set_active(self, active):
        with self._lock:
            self._active = bool(active)
            if not self._active:
                self._current_target = None

    def update_cursor_pos(self, x, y):
        with self._lock:
            self._cursor_pos = (int(x), int(y))

    def get_target(self):
        with self._lock:
            return self._current_target

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
            # Check invoke pattern (clickable)
            try:
                if wrapper.is_invoke_pattern_available():
                    return True
            except:
                pass
            return False
        except:
            return False

    def run(self):
        with open("snap_debug.txt", "w", encoding="utf-8") as f:
            f.write(f"SmartSnapper: Started. Available={self.available}\n")

        if not self.available:
            with open("snap_debug.txt", "a", encoding="utf-8") as f:
                f.write("Pywinauto not available!\n")
            return

        try:
            desktop = Desktop(backend='uia')
            with open("snap_debug.txt", "a", encoding="utf-8") as f:
                f.write("Desktop OK\n")
        except Exception as e:
            with open("snap_debug.txt", "a", encoding="utf-8") as f:
                f.write(f"Desktop failed: {e}\n")
            return
        
        loop_count = 0
        
        while self._running:
            try:
                with self._lock:
                    active = self._active
                    pos = self._cursor_pos
                
                if not active or pos is None:
                    time.sleep(Config.SNAP_INTERVAL)
                    continue

                loop_count += 1
                x, y = pos
                target = None
                
                # Get element at cursor
                wrapper = None
                try:
                    wrapper = desktop.from_point(x, y)
                except Exception as e:
                    if loop_count % 20 == 1:
                        with open("snap_debug.txt", "a", encoding="utf-8") as f:
                            f.write(f"from_point error: {e}\n")
                
                if wrapper:
                    # Find interactive element (current or parent)
                    curr = wrapper
                    found = None
                    path = []
                    
                    for _ in range(6):
                        try:
                            ctype = curr.friendly_class_name()
                            path.append(ctype)
                            
                            if self._is_interactive(curr):
                                found = curr
                                break
                            
                            parent = curr.parent()
                            if not parent:
                                break
                            curr = parent
                        except:
                            break
                    
                    if found:
                        try:
                            rect = found.rectangle()
                            cx = rect.left + rect.width() / 2
                            cy = rect.top + rect.height() / 2
                            ctype = found.friendly_class_name()
                            
                            dx = cx - x
                            dy = cy - y
                            dist = math.hypot(dx, dy)
                            
                            if dist <= Config.SNAP_RADIUS:
                                target = (float(cx), float(cy))
                                
                                # Log occasionally
                                if loop_count % 10 == 1:
                                    with open("snap_debug.txt", "a", encoding="utf-8") as f:
                                        f.write(f"Target: {ctype} @ {int(cx)},{int(cy)} dist={int(dist)}\n")
                        except:
                            pass
                    else:
                        # Log what we found
                        if loop_count % 30 == 1:
                            with open("snap_debug.txt", "a", encoding="utf-8") as f:
                                f.write(f"No target. Path: {' > '.join(path[:4])}\n")

                with self._lock:
                    self._current_target = target

                time.sleep(Config.SNAP_INTERVAL)

            except Exception as e:
                with open("snap_debug.txt", "a", encoding="utf-8") as f:
                    f.write(f"Loop error: {e}\n")
                time.sleep(0.2)
