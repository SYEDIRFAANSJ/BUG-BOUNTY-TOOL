import pytest
import time
from recon.rate_limiter import RateLimiter

def test_acquire_within_limit(redis_client):
    limiter = RateLimiter(redis_client, key="test_limit", limit=5, window=1)
    for _ in range(5):
        assert limiter.acquire() is True

def test_acquire_blocks_when_exhausted(redis_client):
    limiter = RateLimiter(redis_client, key="test_exhausted", limit=2, window=1)
    limiter.acquire()
    limiter.acquire()
    start_time = time.time()
    limiter.acquire() # Should block
    end_time = time.time()
    assert end_time - start_time >= 0.9

def test_tokens_refill(redis_client):
    limiter = RateLimiter(redis_client, key="test_refill", limit=1, window=1)
    limiter.acquire()
    time.sleep(1.1)
    start_time = time.time()
    limiter.acquire() # Should not block long
    end_time = time.time()
    assert end_time - start_time < 0.5
