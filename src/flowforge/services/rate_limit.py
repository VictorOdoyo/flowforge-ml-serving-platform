import time

from redis.asyncio import Redis


class FixedWindowRateLimiter:
    def __init__(self, redis: Redis, *, limit: int, window_seconds: int = 60) -> None:
        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds

    async def allow(self, identity: str) -> tuple[bool, int]:
        window = int(time.time()) // self.window_seconds
        key = f"rate-limit:{identity}:{window}"
        async with self.redis.pipeline(transaction=True) as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, self.window_seconds + 1)
            count, _ = await pipeline.execute()
        remaining = max(self.limit - int(count), 0)
        return int(count) <= self.limit, remaining
