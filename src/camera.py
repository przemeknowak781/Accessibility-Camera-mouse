import cv2
import threading
import time

class ThreadedCamera:
    def __init__(self, source=0, width=640, height=480, backend="auto"):
        self.capture, self.backend = self._open_capture(source, width, height, backend)
        self.success, self.frame = self.capture.read()
        self.frame_id = 0
        self.frame_time = time.time() if self.success else None
        self.av_fps = 0
        self.stopped = False
        self.lock = threading.Lock()

    def _open_capture(self, source, width, height, backend):
        backend = (backend or "auto").lower()
        candidates = []
        if backend == "auto":
            candidates = [
                ("msmf", cv2.CAP_MSMF),
                ("dshow", cv2.CAP_DSHOW),
                ("any", None),
            ]
        elif backend == "msmf":
            candidates = [("msmf", cv2.CAP_MSMF)]
        elif backend == "dshow":
            candidates = [("dshow", cv2.CAP_DSHOW)]
        else:
            candidates = [(backend, None)]

        last = None
        for name, cap_backend in candidates:
            if cap_backend is None:
                cap = cv2.VideoCapture(source)
            else:
                cap = cv2.VideoCapture(source, cap_backend)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            ok, frame = cap.read()
            if ok and frame is not None:
                return cap, name
            last = cap
        return last if last is not None else cv2.VideoCapture(source), backend
        
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
                    self.success = True
                    self.frame = frame
                    self.frame_id += 1
                    self.frame_time = time.time()
                else:
                    self.success = False
            
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
            if not success:
                time.sleep(0.01)

    def read(self):
        with self.lock:
            frame = self.frame.copy() if self.frame is not None else None
            return self.success, frame, self.frame_id, self.frame_time

    def release(self):
        self.stopped = True
        self.capture.release()
