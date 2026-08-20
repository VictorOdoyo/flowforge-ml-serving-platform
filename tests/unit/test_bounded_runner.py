import asyncio

import pytest

from flowforge.services.bounded_runner import run_bounded


async def test_run_bounded_preserves_result_order() -> None:
    async def worker(value: int) -> int:
        await asyncio.sleep(0)
        return value * 2

    assert await run_bounded([3, 1, 2], worker, concurrency=2) == [6, 2, 4]


async def test_run_bounded_limits_concurrent_work() -> None:
    active = 0
    peak = 0

    async def worker(value: int) -> int:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return value

    assert await run_bounded([1, 2, 3, 4], worker, concurrency=2) == [1, 2, 3, 4]
    assert peak == 2


async def test_run_bounded_times_out_slow_work() -> None:
    async def worker(value: int) -> int:
        await asyncio.sleep(1)
        return value

    with pytest.raises(TimeoutError):
        await run_bounded([1], worker, concurrency=1, timeout_seconds=0.01)


async def test_run_bounded_rejects_zero_concurrency() -> None:
    async def worker(value: int) -> int:
        return value

    with pytest.raises(ValueError, match="concurrency"):
        await run_bounded([1], worker, concurrency=0)
