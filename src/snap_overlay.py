"""
Snap target marker - small window that follows the snap target.
Uses a tiny always-on-top window instead of drawing on desktop.
"""
import threading
import tkinter as tk


class SnapMarker:
    """Small marker window showing snap target location."""
    
    def __init__(self):
        self._target = None
        self._lock = threading.Lock()
        self._running = False
        self._root = None
        
    def start(self):
        """Start marker in separate thread."""
        self._running = True
        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        
    def stop(self):
        """Stop marker."""
        self._running = False
        if self._root:
            try:
                self._root.quit()
            except:
                pass
    
    def set_target(self, target):
        """Set target position: (x, y) or None to hide."""
        with self._lock:
            self._target = target
    
    def _run(self):
        """Main loop."""
        try:
            self._root = tk.Tk()
            self._root.title("")
            
            # Small window size
            size = 50
            
            # Configure window
            self._root.overrideredirect(True)  # No title bar
            self._root.attributes('-topmost', True)
            self._root.attributes('-transparentcolor', '#ff00ff')
            self._root.config(bg='#ff00ff')
            self._root.geometry(f"{size}x{size}+0+0")
            
            # Canvas with crosshair
            canvas = tk.Canvas(
                self._root,
                width=size,
                height=size,
                bg='#ff00ff',
                highlightthickness=0
            )
            canvas.pack()
            
            # Draw crosshair (stays static, window moves)
            center = size // 2
            r = 18
            # Circle
            canvas.create_oval(
                center - r, center - r, center + r, center + r,
                outline='#FF6600', width=3
            )
            # Center dot
            canvas.create_oval(
                center - 4, center - 4, center + 4, center + 4,
                fill='#FF6600', outline='#FF6600'
            )
            # Crosshair lines
            canvas.create_line(center - r - 8, center, center - r + 5, center, fill='#FF6600', width=2)
            canvas.create_line(center + r - 5, center, center + r + 8, center, fill='#FF6600', width=2)
            canvas.create_line(center, center - r - 8, center, center - r + 5, fill='#FF6600', width=2)
            canvas.create_line(center, center + r - 5, center, center + r + 8, fill='#FF6600', width=2)
            
            self._root.update()
            
            # Make click-through
            try:
                import ctypes
                hwnd = self._root.winfo_id()
                GWL_EXSTYLE = -20
                WS_EX_LAYERED = 0x80000
                WS_EX_TRANSPARENT = 0x20
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
            except:
                pass
            
            # Hide initially
            self._root.withdraw()
            
            # Update loop
            def update():
                if not self._running:
                    self._root.quit()
                    return
                    
                with self._lock:
                    target = self._target
                
                if target:
                    x, y = int(target[0]), int(target[1])
                    # Position window centered on target
                    self._root.geometry(f"+{x - size//2}+{y - size//2}")
                    self._root.deiconify()
                else:
                    self._root.withdraw()
                
                self._root.after(30, update)  # ~30 FPS
            
            update()
            self._root.mainloop()
            
        except Exception as e:
            print(f"SnapMarker error: {e}")


# Alias for compatibility
GDIOverlay = SnapMarker
