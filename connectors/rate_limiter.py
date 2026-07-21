import time
import threading

class TokenBucketRateLimiter:
    def __init__(self, rate_per_minute: int):
        self.rate_per_minute = rate_per_minute
        self.capacity = rate_per_minute
        self.tokens = float(rate_per_minute)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()
        self.refill_rate = rate_per_minute / 60.0

    def acquire(self):
        with self.lock:
            while True:
                now = time.monotonic()
                time_passed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
                self.last_refill = now
                
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                else:
                    sleep_time = (1.0 - self.tokens) / self.refill_rate
                    time.sleep(sleep_time)
