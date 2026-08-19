from datetime import UTC, datetime
from uuid import UUID

from flowforge.core.exceptions import ResourceNotFoundError
from flowforge.models.enums import JobStatus, JobType, UserRole
from flowforge.models.job import Job
from flowforge.repositories.audit import AuditRepository
from flowforge.repositories.job import JobRepository
from flowforge.schemas.common import Page
from flowforge.schemas.job import JobCreate, JobRead
from flowforge.services.dispatcher import JobDispatcher
from flowforge.services.state_machine import ensure_job_transition


class JobService:
    def __init__(
        self,
        jobs: JobRepository,
        audits: AuditRepository,
        dispatcher: JobDispatcher,
    ) -> None:
        self.jobs = jobs
        self.audits = audits
        self.dispatcher = dispatcher

    async def submit(self, owner_id: UUID, data: JobCreate) -> Job:
        job = await self.jobs.create(owner_id, data)
        await self.audits.record(
            action="job.created",
            resource_type="job",
            resource_id=str(job.id),
            actor_id=owner_id,
            job_id=job.id,
            detail={"type": job.job_type.value, "priority": job.priority},
        )
        await self.jobs.commit()
        try:
            receipt = self.dispatcher.enqueue(job.id)
            await self.jobs.set_task_id(job, receipt.task_id)
            await self.jobs.commit()
        except Exception:
            await self.jobs.rollback()
            raise
        return job

    async def get(self, job_id: UUID) -> Job:
        job = await self.jobs.get(job_id)
        if job is None:
            raise ResourceNotFoundError("Job was not found", context={"job_id": str(job_id)})
        return job

    async def list(
        self,
        *,
        requester_id: UUID,
        role: UserRole,
        status: JobStatus | None,
        job_type: JobType | None,
        limit: int,
        offset: int,
    ) -> Page[JobRead]:
        owner_id = None if role == UserRole.ADMIN else requester_id
        rows = await self.jobs.list(
            owner_id=owner_id,
            status=status,
            job_type=job_type,
            limit=limit,
            offset=offset,
        )
        total = await self.jobs.count(owner_id=owner_id, status=status, job_type=job_type)
        return Page[JobRead](
            items=[JobRead.model_validate(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def cancel(self, job_id: UUID, actor_id: UUID) -> Job:
        job = await self.get(job_id)
        ensure_job_transition(job.status, JobStatus.CANCELLED)
        job.status = JobStatus.CANCELLED
        job.finished_at = datetime.now(UTC)
        await self.audits.record(
            action="job.cancelled",
            resource_type="job",
            resource_id=str(job.id),
            actor_id=actor_id,
            job_id=job.id,
        )
        await self.jobs.commit()
        return job

