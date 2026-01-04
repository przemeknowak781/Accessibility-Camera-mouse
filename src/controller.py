import time
from src.config import Config

class MouseController:
    def __init__(self, backend="auto"):
        self.backend = None
        self.prefer_backend = backend
        self.mouse = None
        self.button = None
        self.screen_size = None
        self.screen_bounds = None
        self._load_backend()
        self.click_ready = True
        self.last_click_time = 0.0
        self.click_cooldown = Config.CLICK_COOLDOWN
        self.blink_cooldown = Config.BLINK_COOLDOWN
        self.drag_active = False

    def _load_backend(self):
        if self.prefer_backend == "pynput":
            self._load_pynput()
            return
        try:
            import autopy
            self.backend = 'autopy'
            self.mouse = autopy.mouse
            self.screen_size = autopy.screen.size()
        except Exception:
            self._load_pynput()

    def _load_pynput(self):
        from pynput.mouse import Button, Controller
        self.backend = 'pynput'
        self.mouse = Controller()
        self.button = Button

    def move(self, x, y):
        if self.backend == 'autopy':
            if self.screen_size:
                max_x = max(self.screen_size[0] - 1, 0)
                max_y = max(self.screen_size[1] - 1, 0)
                x = max(0, min(x, max_x))
                y = max(0, min(y, max_y))
            self.mouse.move(x, y)
        else:
            if self.screen_bounds:
                min_x, min_y, max_x, max_y = self.screen_bounds
                x = max(min_x, min(x, max_x))
                y = max(min_y, min(y, max_y))
            self.mouse.position = (x, y)

    def set_bounds(self, min_x, min_y, max_x, max_y):
        self.screen_bounds = (min_x, min_y, max_x, max_y)

    def get_position(self):
        if self.backend == 'autopy':
            return self.mouse.location()
        else:
            return self.mouse.position

    def click(self):
        if self.backend == 'autopy':
            self.mouse.click()
        else:
            self.mouse.click(self.button.left, 1)

    def press(self):
        if self.backend == 'autopy':
            try:
                self.mouse.toggle(self.mouse.Button.LEFT, True)
            except TypeError:
                self.mouse.toggle(True, self.mouse.Button.LEFT)
        else:
            self.mouse.press(self.button.left)

    def release(self):
        if self.backend == 'autopy':
            try:
                self.mouse.toggle(self.mouse.Button.LEFT, False)
            except TypeError:
                self.mouse.toggle(False, self.mouse.Button.LEFT)
        else:
            self.mouse.release(self.button.left)

    def update_click(self, distance):
        threshold = Config.CLICK_THRESHOLD
        now = time.time()
        
        if distance < threshold:
            if self.click_ready and (now - self.last_click_time > self.click_cooldown):
                self.click()
                self.last_click_time = now
                self.click_ready = False
                return True
        elif distance > threshold * 1.5: # Hysteresis: wait until fingers are far apart (30 * 1.5 = 45px)
            self.click_ready = True
            
        return False

    def update_blink(self, blinked):
        if not blinked:
            return False
        now = time.time()
        if now - self.last_click_time > self.blink_cooldown:
            self.click()
            self.last_click_time = now
            return True
        return False

    def update_drag(self, distance):
        threshold = Config.CLICK_THRESHOLD
        if not self.drag_active and distance < threshold:
            self.press()
            self.drag_active = True
            return True
        if self.drag_active and distance > threshold * 1.2:
            self.release()
            self.drag_active = False
        return self.drag_active
