from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.models.model_version import ModelVersion


class ModelVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, model_id: UUID) -> ModelVersion | None:
        return await self.session.get(ModelVersion, model_id)

    async def list(self, *, limit: int, offset: int) -> list[ModelVersion]:
        statement = select(ModelVersion).order_by(ModelVersion.created_at.desc())
        return list((await self.session.scalars(statement.limit(limit).offset(offset))).all())

    async def add(self, model: ModelVersion) -> ModelVersion:
        self.session.add(model)
        await self.session.flush()
        return model

    async def commit(self) -> None:
        await self.session.commit()
