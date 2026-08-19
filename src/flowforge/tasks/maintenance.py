import asyncio

from flowforge.repositories.idempotency import IdempotencyRepository
from flowforge.tasks.celery_app import celery_app
from flowforge.db.session import session_factory


async def cleanup_idempotency_async() -> int:
    async with session_factory() as session:
        deleted = await IdempotencyRepository(session).delete_expired()
        await session.commit()
        return deleted


@celery_app.task(name="flowforge.cleanup_idempotency")
def cleanup_idempotency() -> int:
    return asyncio.run(cleanup_idempotency_async())

