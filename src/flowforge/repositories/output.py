from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.models.output import JobOutput


class OutputRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_job(self, job_id: UUID) -> list[JobOutput]:
        statement = (
            select(JobOutput).where(JobOutput.job_id == job_id).order_by(JobOutput.created_at)
        )
        return list((await self.session.scalars(statement)).all())

    async def add(self, output: JobOutput) -> JobOutput:
        self.session.add(output)
        await self.session.flush()
        return output

