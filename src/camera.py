import cv2
import threading
import time

class ThreadedCamera:
    def __init__(self, source=0, width=640, height=480):
        self.capture = cv2.VideoCapture(source)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        self.success, self.frame = self.capture.read()
        self.av_fps = 0
        self.stopped = False
        self.lock = threading.Lock()
        
    def start(self):
        t = threading.Thread(target=self._update, args=(), daemon=True)
        t.start()
        return self
        
    def _update(self):
        last_time = time.time()
        fps_filter = 0
        
        while not self.stopped:
            success, frame = self.capture.read()
            with self.lock:
                if success:
                    self.success = success
                    self.frame = frame
                else:
                    self.stopped = True
            
            # FPS Calculation for monitoring camera thread health
            now = time.time()
            dt = now - last_time
            last_time = now
            if dt > 0:
                fps = 1.0 / dt
                fps_filter = 0.9 * fps_filter + 0.1 * fps 
                self.av_fps = fps_filter
            
            # Small sleep to prevent busy spinning if camera is slow, 
            # though usually read() blocks until next frame is ready.
            # time.sleep(0.001) 

    def read(self):
        with self.lock:
            return self.success, self.frame.copy() if self.frame is not None else None

    def release(self):
        self.stopped = True
        self.capture.release()
