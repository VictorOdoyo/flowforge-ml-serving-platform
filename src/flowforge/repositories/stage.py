from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.models.stage import ProcessingStage


class StageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_job(self, job_id: UUID) -> list[ProcessingStage]:
        statement = (
            select(ProcessingStage)
            .where(ProcessingStage.job_id == job_id)
            .order_by(ProcessingStage.sequence)
        )
        return list((await self.session.scalars(statement)).all())

    async def add_many(self, stages: list[ProcessingStage]) -> None:
        self.session.add_all(stages)
        await self.session.flush()

