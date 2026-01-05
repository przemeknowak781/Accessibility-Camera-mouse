import ctypes

import cv2
import numpy as np
from screeninfo import get_monitors


def set_window_topmost(window_name, topmost=True):
    """Set an OpenCV window to always-on-top on Windows."""
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, window_name)
        if hwnd:
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            target = HWND_TOPMOST if topmost else HWND_NOTOPMOST
            ctypes.windll.user32.SetWindowPos(
                hwnd,
                target,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
    except Exception:
        pass


def enforce_window_topmost(window_name):
    try:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
    except Exception:
        pass
    set_window_topmost(window_name, True)


def get_mini_window_size(max_w=320, aspect=16 / 9):
    max_w = max(int(max_w), 1)
    width = max_w
    height = max(int(round(width / aspect)), 1)
    return width, height


def resize_with_letterbox(frame, target_w, target_h):
    src_h, src_w = frame.shape[:2]
    scale = min(target_w / max(src_w, 1), target_h / max(src_h, 1))
    new_w = max(int(round(src_w * scale)), 1)
    new_h = max(int(round(src_h * scale)), 1)
    resized = cv2.resize(frame, (new_w, new_h))
    output = np.zeros((target_h, target_w, 3), dtype=frame.dtype)
    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    output[y : y + new_h, x : x + new_w] = resized
    return output


def position_mini_window(window_name, screen_x, screen_y, screen_w, screen_h, win_w, win_h):
    margin = 16
    x = screen_x + margin
    y = screen_y + margin
    cv2.moveWindow(window_name, max(screen_x, x), max(screen_y, y))


def get_monitor_layout(monitor_index):
    monitors = get_monitors()
    if not monitors:
        return (1920, 1080, 0, 0), (0, 0, 1919, 1079)

    if 0 <= monitor_index < len(monitors):
        monitor = monitors[monitor_index]
    else:
        monitor = next(
            (m for m in monitors if getattr(m, "is_primary", False)), monitors[0]
        )
    bounds = (
        monitor.x,
        monitor.y,
        monitor.x + monitor.width - 1,
        monitor.y + monitor.height - 1,
    )
    return (monitor.width, monitor.height, monitor.x, monitor.y), bounds

