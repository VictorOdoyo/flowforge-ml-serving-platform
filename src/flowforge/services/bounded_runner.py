import asyncio
from collections.abc import Awaitable, Callable, Iterable


async def run_bounded[InputT, OutputT](
    items: Iterable[InputT],
    worker: Callable[[InputT], Awaitable[OutputT]],
    *,
    concurrency: int,
    timeout_seconds: float | None = None,
) -> list[OutputT]:
    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")

    semaphore = asyncio.Semaphore(concurrency)

    async def run_one(item: InputT) -> OutputT:
        async with semaphore:
            task = worker(item)
            if timeout_seconds is None:
                return await task
            return await asyncio.wait_for(task, timeout=timeout_seconds)

    return await asyncio.gather(*(run_one(item) for item in items))
