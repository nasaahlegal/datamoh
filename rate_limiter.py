import time
from threading import Lock

class RateLimiter:
    def __init__(self, calls=3, period=10):
        self.calls = calls
        self.period = period
        self.timestamps = {}
        self.lock = Lock()

    def is_allowed(self, user_id):
        now = time.time()
        with self.lock:
            user_times = self.timestamps.get(user_id, [])
            user_times = [t for t in user_times if now - t < self.period]
            if len(user_times) >= self.calls:
                return False
            user_times.append(now)
            self.timestamps[user_id] = user_times
            return True

rate_limiter = RateLimiter(calls=3, period=10)