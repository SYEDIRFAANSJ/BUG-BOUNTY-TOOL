"""
Redis client factory — provides a synchronous Redis client.

Celery tasks, monitor, and circuit breaker all use sync Redis calls.
For async contexts (FastAPI WebSocket), use redis.asyncio separately.
"""

import redis
from functools import lru_cache


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    """Return a cached synchronous Redis client."""
    from shared.config import settings
    return redis.from_url(settings.redis_url, decode_responses=True)


# Alias for backward compatibility with modules importing get_redis
get_redis = get_redis_client


def get_async_redis():
    """Return an async Redis client for WebSocket pub/sub."""
    import redis.asyncio as aioredis
    from shared.config import settings
    return aioredis.from_url(settings.redis_url, decode_responses=True)
