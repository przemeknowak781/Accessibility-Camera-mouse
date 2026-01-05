import time
import threading
import math
from src.config import Config

class MouseDriver:
    def __init__(self, controller):
        self.controller = controller
        self.target_x = None
        self.target_y = None
        
        self.curr_x = None
        self.curr_y = None
        
        self.vel_x = 0.0
        self.vel_y = 0.0
        
        self.last_update_time = 0.0
        self.running = False
        self.paused = False
        self.lock = threading.Lock()
        self.snap_target = None
        
        # Smoothing settings
        self.refresh_rate = getattr(Config, 'MOUSE_REFRESH_RATE', 120)
        self.friction = getattr(Config, 'MOUSE_FRICTION', 0.90)
        self.prediction_decay = getattr(Config, 'MOUSE_PREDICTION_DECAY', 0.1) # How fast prediction fades
        self.speed_coeff = getattr(Config, 'MOUSE_SPEED_COEFF', 15.0) # For exponential smoothing
        self.coast_window = getattr(Config, 'COAST_WINDOW', 0.4)
        self.override_dist = getattr(Config, 'MOUSE_OVERRIDE_DIST', 80.0)
        self.override_timeout = getattr(Config, 'MOUSE_OVERRIDE_TIMEOUT', 1.0)
        self._override_until = 0.0

    def set_snap_target(self, target):
        with self.lock:
            self.snap_target = target
        
    def start(self):
        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        
    def stop(self):
        self.running = False

    def pause(self):
        with self.lock:
            self.paused = True

    def resume(self):
        with self.lock:
            self.paused = False

    def update_target(self, x, y, timestamp=None):
        with self.lock:
            # If this is the first update, snap immediately
            if self.curr_x is None:
                self.curr_x = x
                self.curr_y = y
                
            self.target_x = x
            self.target_y = y
            self.last_update_time = time.time() if timestamp is None else float(timestamp)

    def get_last_pos(self):
        """Returns the current estimated or real position of the mouse."""
        with self.lock:
            if self.curr_x is None:
                real_x, real_y = self.controller.get_position()
                return float(real_x), float(real_y)
            return float(self.curr_x), float(self.curr_y)

    def step(self, now, real_x, real_y, dt):
        with self.lock:
            is_paused = self.paused

        if is_paused:
            with self.lock:
                self.curr_x = real_x
                self.curr_y = real_y
                self.target_x = real_x
                self.target_y = real_y
                self.vel_x = 0.0
                self.vel_y = 0.0
                self.last_update_time = now
            return

        if self.curr_x is None:
            self.curr_x, self.curr_y = real_x, real_y

        dist = math.hypot(real_x - self.curr_x, real_y - self.curr_y)
        if dist > self.override_dist:
            self._override_until = now + self.override_timeout
            with self.lock:
                self.curr_x = real_x
                self.curr_y = real_y
                self.vel_x = 0.0
                self.vel_y = 0.0

        if now < self._override_until:
            with self.lock:
                self.curr_x = real_x
                self.curr_y = real_y
                self.target_x = real_x
                self.target_y = real_y
            return

        with self.lock:
            target_x, target_y = self.target_x, self.target_y
            curr_x, curr_y = self.curr_x, self.curr_y
            last_update = self.last_update_time
            snap_target = self.snap_target

        if curr_x is None or target_x is None:
            return

        time_since_update = now - last_update

        if (
            snap_target is not None
            and target_x is not None
            and curr_x is not None
            and curr_y is not None
        ):
            speed = math.hypot(self.vel_x, self.vel_y)
            if speed < Config.SNAP_BREAKOUT_SPEED:
                lock_radius = max(0.0, getattr(Config, "SNAP_LOCK_RADIUS", 0.0))
                if lock_radius > 0.0:
                    dist = math.hypot(snap_target[0] - curr_x, snap_target[1] - curr_y)
                    if dist <= lock_radius:
                        snap_x, snap_y = snap_target
                        with self.lock:
                            self.curr_x = snap_x
                            self.curr_y = snap_y
                            self.target_x = snap_x
                            self.target_y = snap_y
                            self.vel_x = 0.0
                            self.vel_y = 0.0
                        self.controller.move(snap_x, snap_y)
                        return

        if time_since_update < 0.1:
            if snap_target is not None and target_x is not None:
                speed = math.hypot(self.vel_x, self.vel_y)
                target_x, target_y = self._apply_snap(
                    target_x, target_y, curr_x, curr_y, snap_target, speed
                )
            diff_x = target_x - curr_x
            diff_y = target_y - curr_y

            vx = diff_x * self.speed_coeff
            vy = diff_y * self.speed_coeff

            move_x = vx * dt
            move_y = vy * dt

            curr_x += move_x
            curr_y += move_y

            with self.lock:
                self.curr_x = curr_x
                self.curr_y = curr_y
                self.vel_x = vx
                self.vel_y = vy
        elif time_since_update < self.coast_window:
            with self.lock:
                self.vel_x *= self.friction
                self.vel_y *= self.friction
                self.curr_x += self.vel_x * dt
                self.curr_y += self.vel_y * dt

        with self.lock:
            out_x, out_y = self.curr_x, self.curr_y

        self.controller.move(out_x, out_y)

    def _apply_snap(self, target_x, target_y, curr_x, curr_y, snap_target, speed):
        if not getattr(Config, "SNAP_ENABLED", False):
            return target_x, target_y
        if speed >= Config.SNAP_BREAKOUT_SPEED:
            return target_x, target_y
        snap_x, snap_y = snap_target
        dx = snap_x - target_x
        dy = snap_y - target_y
        dist = math.hypot(dx, dy)
        if dist > Config.SNAP_RADIUS:
            return target_x, target_y
        lock_radius = max(0.0, getattr(Config, "SNAP_LOCK_RADIUS", 0.0))
        lock_strength = max(0.0, min(getattr(Config, "SNAP_LOCK_STRENGTH", 1.0), 1.0))
        base_strength = max(0.0, min(Config.SNAP_STRENGTH, 1.0))
        if lock_radius > 0.0 and dist <= lock_radius:
            return snap_x, snap_y
        strength = base_strength
        if Config.SNAP_RADIUS > lock_radius:
            t = (dist - lock_radius) / (Config.SNAP_RADIUS - lock_radius)
            t = max(0.0, min(1.0, t))
            strength = lock_strength + (base_strength - lock_strength) * t
        target_x += dx * strength
        target_y += dy * strength
        return target_x, target_y

    def _loop(self):
        dt = 1.0 / self.refresh_rate
        while self.running:
            start_time = time.time()
            now = time.time()
            real_x, real_y = self.controller.get_position()
            self.step(now, real_x, real_y, dt)
            elapsed = time.time() - start_time
            sleep_time = max(0, dt - elapsed)
            time.sleep(sleep_time)
