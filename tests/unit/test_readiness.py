from typing import Any

import pytest
from redis.exceptions import RedisError

from flowforge.services import readiness
from flowforge.services.readiness import ReadinessService, redis_is_ready


class FakeRedis:
    def __init__(self, result: bool | Exception) -> None:
        self.result = result

    async def ping(self) -> bool:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


async def test_redis_is_ready_returns_true_when_ping_succeeds() -> None:
    assert await redis_is_ready(FakeRedis(True)) is True  # type: ignore[arg-type]


@pytest.mark.parametrize("error", [OSError("offline"), RedisError("offline")])
async def test_redis_is_ready_returns_false_for_connection_errors(error: Exception) -> None:
    assert await redis_is_ready(FakeRedis(error)) is False  # type: ignore[arg-type]


async def test_readiness_service_combines_dependency_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def database_ready(_: Any) -> bool:
        return True

    async def cache_ready(_: Any) -> bool:
        return False

    monkeypatch.setattr(
        readiness,
        "database_is_ready",
        database_ready,
    )
    monkeypatch.setattr(
        readiness,
        "redis_is_ready",
        cache_ready,
    )

    service = ReadinessService(engine=object(), redis=object())  # type: ignore[arg-type]

    assert await service.checks() == {"api": True, "database": True, "redis": False}
