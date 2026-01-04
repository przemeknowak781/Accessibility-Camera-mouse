import time
from collections import deque


class EventLog:
    def __init__(self, path="events.log", max_events=8):
        self.path = path
        self.events = deque(maxlen=max_events)

    def add(self, event, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        stamp = time.strftime("%H:%M:%S", time.localtime(timestamp))
        line = f"{stamp} {event}"
        self.events.appendleft(line)
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def recent(self):
        return list(self.events)
