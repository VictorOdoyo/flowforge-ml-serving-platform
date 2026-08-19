from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.models.idempotency import IdempotencyRecord


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, scope: str, key: str) -> IdempotencyRecord | None:
        statement = select(IdempotencyRecord).where(
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.key == key,
            IdempotencyRecord.expires_at > datetime.now(UTC),
        )
        return await self.session.scalar(statement)

    async def add(self, record: IdempotencyRecord) -> IdempotencyRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def delete_expired(self) -> int:
        result = await self.session.execute(
            delete(IdempotencyRecord).where(
                IdempotencyRecord.expires_at <= datetime.now(UTC)
            )
        )
        return int(result.rowcount or 0)  # type: ignore[attr-defined]

