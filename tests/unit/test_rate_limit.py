from types import TracebackType
from typing import cast

import pytest
from redis.asyncio import Redis

from flowforge.services.rate_limit import FixedWindowRateLimiter


class FakePipeline:
    def __init__(self, count: int) -> None:
        self.count = count
        self.keys: list[str] = []

    async def __aenter__(self) -> "FakePipeline":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def incr(self, key: str) -> "FakePipeline":
        self.keys.append(key)
        return self

    def expire(self, key: str, seconds: int) -> "FakePipeline":
        self.keys.append(f"{key}:{seconds}")
        return self

    async def execute(self) -> tuple[int, bool]:
        return self.count, True


class FakeRedis:
    def __init__(self, count: int) -> None:
        self.pipeline_instance = FakePipeline(count)

    def pipeline(self, *, transaction: bool) -> FakePipeline:
        assert transaction
        return self.pipeline_instance


@pytest.mark.asyncio
async def test_allows_requests_below_fixed_window_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = FakeRedis(count=3)
    monkeypatch.setattr("flowforge.services.rate_limit.time.time", lambda: 1_800.0)
    limiter = FixedWindowRateLimiter(cast(Redis, redis), limit=5, window_seconds=60)

    allowed, remaining = await limiter.allow("user-42")

    assert allowed
    assert remaining == 2
    assert redis.pipeline_instance.keys[0] == "rate-limit:user-42:30"


@pytest.mark.asyncio
async def test_rejects_requests_above_fixed_window_limit() -> None:
    limiter = FixedWindowRateLimiter(cast(Redis, FakeRedis(count=6)), limit=5)

    allowed, remaining = await limiter.allow("user-42")

    assert not allowed
    assert remaining == 0
