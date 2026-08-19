from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.models.enums import JobStatus, JobType
from flowforge.models.job import Job
from flowforge.schemas.job import JobCreate


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, owner_id: UUID, data: JobCreate) -> Job:
        job = Job(
            owner_id=owner_id,
            model_version_id=data.model_version_id,
            name=data.name,
            job_type=data.job_type,
            payload=data.payload,
            priority=data.priority,
            max_attempts=data.max_attempts,
            queued_at=datetime.now(UTC),
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get(self, job_id: UUID) -> Job | None:
        return await self.session.get(Job, job_id)

    async def list(
        self,
        *,
        owner_id: UUID | None,
        status: JobStatus | None,
        job_type: JobType | None,
        limit: int,
        offset: int,
    ) -> list[Job]:
        statement = self._filtered(owner_id=owner_id, status=status, job_type=job_type)
        statement = statement.order_by(Job.created_at.desc()).limit(limit).offset(offset)
        return list((await self.session.scalars(statement)).all())

    async def count(
        self,
        *,
        owner_id: UUID | None,
        status: JobStatus | None,
        job_type: JobType | None,
    ) -> int:
        filters = []
        if owner_id is not None:
            filters.append(Job.owner_id == owner_id)
        if status is not None:
            filters.append(Job.status == status)
        if job_type is not None:
            filters.append(Job.job_type == job_type)
        statement = select(func.count(Job.id)).where(*filters)
        return int((await self.session.scalar(statement)) or 0)

    async def set_task_id(self, job: Job, task_id: str) -> None:
        job.task_id = task_id
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    @staticmethod
    def _filtered(
        *, owner_id: UUID | None, status: JobStatus | None, job_type: JobType | None
    ) -> Select[tuple[Job]]:
        statement = select(Job)
        if owner_id is not None:
            statement = statement.where(Job.owner_id == owner_id)
        if status is not None:
            statement = statement.where(Job.status == status)
        if job_type is not None:
            statement = statement.where(Job.job_type == job_type)
        return statement

