import asyncio

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncEngine

from flowforge.db.health import database_is_ready


async def redis_is_ready(redis: Redis) -> bool:
    try:
        return bool(await redis.ping())
    except (OSError, RedisError):
        return False


class ReadinessService:
    def __init__(self, engine: AsyncEngine, redis: Redis) -> None:
        self.engine = engine
        self.redis = redis

    async def checks(self) -> dict[str, bool]:
        database, cache = await asyncio.gather(
            database_is_ready(self.engine),
            redis_is_ready(self.redis),
        )
        return {"api": True, "database": database, "redis": cache}
