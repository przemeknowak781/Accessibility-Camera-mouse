"""
Screen overlay for visualizing snap targets.
Uses tkinter for a transparent always-on-top window.
"""
import tkinter as tk
import threading
import time


class SnapOverlay:
    """Transparent overlay window showing detected UI elements."""
    
    def __init__(self):
        self._elements = []  # List of (x, y, w, h, label) tuples
        self._target = None  # Current snap target (x, y)
        self._cursor = None  # Current cursor position
        self._lock = threading.Lock()
        self._running = False
        self._root = None
        self._canvas = None
        
    def start(self):
        """Start overlay in a separate thread."""
        self._running = True
        t = threading.Thread(target=self._run_tk, daemon=True)
        t.start()
        
    def stop(self):
        """Stop overlay."""
        self._running = False
        if self._root:
            try:
                self._root.quit()
            except:
                pass
    
    def set_elements(self, elements):
        """Set list of detected elements: [(x, y, w, h, label), ...]"""
        with self._lock:
            self._elements = list(elements) if elements else []
            
    def set_target(self, target):
        """Set current snap target: (x, y) or None"""
        with self._lock:
            self._target = target
            
    def set_cursor(self, pos):
        """Set current cursor position: (x, y)"""
        with self._lock:
            self._cursor = pos
    
    def _run_tk(self):
        """Main tkinter loop - runs in separate thread."""
        try:
            self._root = tk.Tk()
            self._root.title("Snap Overlay")
            
            # Get screen size
            screen_w = self._root.winfo_screenwidth()
            screen_h = self._root.winfo_screenheight()
            
            # Make window fullscreen, transparent, click-through
            self._root.geometry(f"{screen_w}x{screen_h}+0+0")
            self._root.overrideredirect(True)  # No title bar
            self._root.attributes('-topmost', True)  # Always on top
            self._root.attributes('-transparentcolor', 'black')  # Black = transparent
            self._root.config(bg='black')
            
            # Make window click-through on Windows
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                # Get the real hwnd of tkinter window
                hwnd = self._root.winfo_id()
                # Extended window style for layered + transparent
                GWL_EXSTYLE = -20
                WS_EX_LAYERED = 0x00080000
                WS_EX_TRANSPARENT = 0x00000020
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, 
                    style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
            except Exception as e:
                print(f"Could not set click-through: {e}")
            
            # Canvas for drawing
            self._canvas = tk.Canvas(
                self._root, 
                width=screen_w, 
                height=screen_h,
                bg='black',
                highlightthickness=0
            )
            self._canvas.pack()
            
            # Start update loop
            self._update()
            
            self._root.mainloop()
        except Exception as e:
            print(f"Overlay error: {e}")
            
    def _update(self):
        """Update overlay drawing."""
        if not self._running or not self._canvas:
            return
            
        # Clear canvas
        self._canvas.delete("all")
        
        with self._lock:
            elements = list(self._elements)
            target = self._target
            cursor = self._cursor
        
        # Draw detected elements as rectangles
        for elem in elements:
            if len(elem) >= 4:
                x, y, w, h = elem[:4]
                label = elem[4] if len(elem) > 4 else ""
                
                # Draw rectangle outline
                self._canvas.create_rectangle(
                    x, y, x + w, y + h,
                    outline='#00FF00',  # Green
                    width=2
                )
                
                # Draw label
                if label:
                    self._canvas.create_text(
                        x + 2, y + 2,
                        text=label,
                        fill='#00FF00',
                        anchor='nw',
                        font=('Arial', 9)
                    )
        
        # Draw snap target as crosshair
        if target:
            tx, ty = target
            size = 20
            # Outer circle
            self._canvas.create_oval(
                tx - size, ty - size, tx + size, ty + size,
                outline='#FF6600',  # Orange
                width=3
            )
            # Inner dot
            self._canvas.create_oval(
                tx - 4, ty - 4, tx + 4, ty + 4,
                fill='#FF6600',
                outline='#FF6600'
            )
            # Crosshair lines
            self._canvas.create_line(tx - size - 5, ty, tx - size + 10, ty, fill='#FF6600', width=2)
            self._canvas.create_line(tx + size - 10, ty, tx + size + 5, ty, fill='#FF6600', width=2)
            self._canvas.create_line(tx, ty - size - 5, tx, ty - size + 10, fill='#FF6600', width=2)
            self._canvas.create_line(tx, ty + size - 10, tx, ty + size + 5, fill='#FF6600', width=2)
        
        # Draw snap radius around cursor
        if cursor:
            cx, cy = cursor
            from src.config import Config
            radius = Config.SNAP_RADIUS
            self._canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline='#3366FF',  # Blue
                width=1,
                dash=(4, 4)
            )
        
        # Schedule next update (30 FPS)
        self._root.after(33, self._update)


# Global overlay instance
_overlay = None

def get_overlay():
    """Get or create global overlay instance."""
    global _overlay
    if _overlay is None:
        _overlay = SnapOverlay()
    return _overlay
