import time
import atexit
from collections import deque


class EventLog:
    def __init__(self, path="events.log", max_events=8, buffer_size=20):
        self.path = path
        self.events = deque(maxlen=max_events)
        self._buffer = []
        self._buffer_size = buffer_size
        atexit.register(self.flush)

    def add(self, event, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        stamp = time.strftime("%H:%M:%S", time.localtime(timestamp))
        line = f"{stamp} {event}"
        self.events.appendleft(line)
        self._buffer.append(line + "\n")
        if len(self._buffer) >= self._buffer_size:
            self.flush()

    def flush(self):
        if self._buffer:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.writelines(self._buffer)
            self._buffer.clear()

    def recent(self):
        return list(self.events)
