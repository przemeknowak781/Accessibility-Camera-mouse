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

        # Snap controller reference (set after construction)
        self.snap_controller = None

        # Smoothing settings
        self.refresh_rate = getattr(Config, "MOUSE_REFRESH_RATE", 120)
        self.friction = getattr(Config, "MOUSE_FRICTION", 0.90)
        self.speed_coeff = getattr(Config, "MOUSE_SPEED_COEFF", 15.0)
        self.coast_window = getattr(Config, "COAST_WINDOW", 0.4)
        self.override_dist = getattr(Config, "MOUSE_OVERRIDE_DIST", 80.0)
        self.override_timeout = getattr(Config, "MOUSE_OVERRIDE_TIMEOUT", 1.0)
        self._override_until = 0.0

    def set_snap_controller(self, snap_controller):
        """Set the snap controller reference for offset calculation."""
        self.snap_controller = snap_controller

    def set_snap_target(self, target):
        """Legacy method - no longer used, snap handled by SnapController."""
        pass

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
        # Single lock acquisition to read all state
        with self.lock:
            is_paused = self.paused
            target_x, target_y = self.target_x, self.target_y
            curr_x, curr_y = self.curr_x, self.curr_y
            last_update = self.last_update_time
            vel_x, vel_y = self.vel_x, self.vel_y

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

        if curr_x is None:
            curr_x, curr_y = real_x, real_y

        dist = math.hypot(real_x - curr_x, real_y - curr_y)
        if dist > self.override_dist:
            self._override_until = now + self.override_timeout
            with self.lock:
                self.curr_x = real_x
                self.curr_y = real_y
                self.vel_x = 0.0
                self.vel_y = 0.0
            return

        if now < self._override_until:
            with self.lock:
                self.curr_x = real_x
                self.curr_y = real_y
                self.target_x = real_x
                self.target_y = real_y
            return

        if curr_x is None or target_x is None:
            return

        time_since_update = now - last_update

        # Calculate movement
        if time_since_update < 0.1:
            diff_x = target_x - curr_x
            diff_y = target_y - curr_y

            vx = diff_x * self.speed_coeff
            vy = diff_y * self.speed_coeff

            move_x = vx * dt
            move_y = vy * dt

            curr_x += move_x
            curr_y += move_y
            vel_x = vx
            vel_y = vy

        elif time_since_update < self.coast_window:
            vel_x *= self.friction
            vel_y *= self.friction
            curr_x += vel_x * dt
            curr_y += vel_y * dt

        # Apply snap offset from SnapController
        if self.snap_controller is not None:
            speed = math.hypot(vel_x, vel_y)
            offset_x, offset_y = self.snap_controller.get_snap_offset(
                curr_x, curr_y, speed, dt
            )
            curr_x += offset_x
            curr_y += offset_y
            # If locked (large offset), zero velocity
            if abs(offset_x) > 1.0 or abs(offset_y) > 1.0:
                vel_x = 0.0
                vel_y = 0.0

        # Single lock acquisition to write all state
        with self.lock:
            self.curr_x = curr_x
            self.curr_y = curr_y
            self.vel_x = vel_x
            self.vel_y = vel_y

        self.controller.move(curr_x, curr_y)

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
