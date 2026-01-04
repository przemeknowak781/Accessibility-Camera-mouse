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
        
        # Smoothing settings
        self.refresh_rate = getattr(Config, 'MOUSE_REFRESH_RATE', 120)
        self.friction = getattr(Config, 'MOUSE_FRICTION', 0.90)
        self.prediction_decay = getattr(Config, 'MOUSE_PREDICTION_DECAY', 0.1) # How fast prediction fades
        self.speed_coeff = getattr(Config, 'MOUSE_SPEED_COEFF', 15.0) # For exponential smoothing
        
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

    def update_target(self, x, y):
        with self.lock:
            # If this is the first update, snap immediately
            if self.curr_x is None:
                self.curr_x = x
                self.curr_y = y
                
            self.target_x = x
            self.target_y = y
            self.last_update_time = time.time()

    def get_last_pos(self):
        """Returns the current estimated or real position of the mouse."""
        with self.lock:
            if self.curr_x is None:
                return 0, 0
            return self.curr_x, self.curr_y

    def _loop(self):
        dt = 1.0 / self.refresh_rate
        override_until = 0.0
        override_dist = getattr(Config, 'MOUSE_OVERRIDE_DIST', 80.0)
        override_timeout = getattr(Config, 'MOUSE_OVERRIDE_TIMEOUT', 1.0)

        while self.running:
            start_time = time.time()
            now = time.time()
            
            # Check Real Position vs Internal Model
            real_x, real_y = self.controller.get_position()

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
                time.sleep(dt)
                continue
            
            # Initialize internal model on first run
            if self.curr_x is None:
                self.curr_x, self.curr_y = real_x, real_y

            # Distance check for manual override detection
            dist = ((real_x - self.curr_x)**2 + (real_y - self.curr_y)**2)**0.5
            
            # If large discrepancy found, assume user moved mouse
            if dist > override_dist:
                override_until = now + override_timeout
                # Sync internal state to real position
                with self.lock:
                    self.curr_x = real_x
                    self.curr_y = real_y
                    self.vel_x = 0
                    self.vel_y = 0
            
            # If in override mode, just sync and skip movement logic
            if now < override_until:
                with self.lock:
                    # Keep syncing to track where user leaves it
                    self.curr_x = real_x
                    self.curr_y = real_y
                    self.target_x = real_x # Avoid snappy jump back
                    self.target_y = real_y
                time.sleep(dt)
                continue

            with self.lock:
                target_x, target_y = self.target_x, self.target_y
                curr_x, curr_y = self.curr_x, self.curr_y
                last_update = self.last_update_time

            if curr_x is None or target_x is None:
                time.sleep(dt)
                continue

            time_since_update = now - last_update
            
            # Logic:
            # 1. If recent update: Move towards target (Smooth pursuit)
            # 2. If NO recent update (lost hand): Coast with current velocity (Momentum)
            
            COAST_WINDOW = getattr(Config, 'COAST_WINDOW', 0.4)
            
            if time_since_update < 0.1: # Active tracking
                # Exponential smoothing (Lerp-like)
                # move proportional to distance
                diff_x = target_x - curr_x
                diff_y = target_y - curr_y
                
                # Simple P-controller for velocity
                # v = distance * speed_coeff
                vx = diff_x * self.speed_coeff
                vy = diff_y * self.speed_coeff
                
                # Apply to current pos
                move_x = vx * dt
                move_y = vy * dt
                
                self.curr_x += move_x
                self.curr_y += move_y
                
                # Update velocity for coasting later
                self.vel_x = vx 
                self.vel_y = vy
                
            elif time_since_update < COAST_WINDOW: # Coasting phase
                # Apply friction to velocity
                self.vel_x *= self.friction
                self.vel_y *= self.friction
                
                self.curr_x += self.vel_x * dt
                self.curr_y += self.vel_y * dt
                
            # Else: Stop moving
            
            # Move the actual mouse
            self.controller.move(self.curr_x, self.curr_y)
            
            elapsed = time.time() - start_time
            sleep_time = max(0, dt - elapsed)
            time.sleep(sleep_time)
