from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from flowforge.core.exceptions import InvalidTransitionError, ResourceNotFoundError
from flowforge.models.enums import JobStatus, JobType, UserRole
from flowforge.models.job import Job
from flowforge.repositories.audit import AuditRepository
from flowforge.repositories.job import JobRepository
from flowforge.schemas.job import JobCreate
from flowforge.services.dispatcher import DispatchReceipt, JobDispatcher
from flowforge.services.job import JobService


class RecordingDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[UUID] = []

    def enqueue(self, job_id: UUID) -> DispatchReceipt:
        self.job_ids.append(job_id)
        return DispatchReceipt(task_id="celery-task-42")


def make_job(
    *,
    owner_id: UUID | None = None,
    status: JobStatus = JobStatus.QUEUED,
) -> Job:
    now = datetime.now(UTC)
    job = Job(
        owner_id=owner_id or uuid4(),
        name="Daily churn scoring",
        job_type=JobType.MODEL_INFERENCE,
        status=status,
        payload={"records": [{"account_id": "A-1"}]},
        priority=70,
        progress=0,
        attempt_count=0,
        max_attempts=3,
        queued_at=now,
    )
    job.id = uuid4()
    job.created_at = now
    job.updated_at = now
    return job


def build_service(
    repository_mock: AsyncMock,
    audit_mock: AsyncMock,
    dispatcher: JobDispatcher,
) -> JobService:
    return JobService(
        jobs=cast(JobRepository, repository_mock),
        audits=cast(AuditRepository, audit_mock),
        dispatcher=dispatcher,
    )


@pytest.mark.asyncio
async def test_submit_persists_audit_and_dispatch_receipt() -> None:
    owner_id = uuid4()
    job = make_job(owner_id=owner_id)
    jobs = AsyncMock(spec=JobRepository)
    audits = AsyncMock(spec=AuditRepository)
    jobs.create.return_value = job
    dispatcher = RecordingDispatcher()
    service = build_service(jobs, audits, dispatcher)

    result = await service.submit(
        owner_id,
        JobCreate(
            name=job.name,
            job_type=job.job_type,
            payload=job.payload,
            priority=job.priority,
        ),
    )

    assert result is job
    assert dispatcher.job_ids == [job.id]
    jobs.set_task_id.assert_awaited_once_with(job, "celery-task-42")
    assert jobs.commit.await_count == 2
    audits.record.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_reports_missing_job() -> None:
    jobs = AsyncMock(spec=JobRepository)
    jobs.get.return_value = None
    service = build_service(jobs, AsyncMock(spec=AuditRepository), RecordingDispatcher())
    job_id = uuid4()

    with pytest.raises(ResourceNotFoundError) as caught:
        await service.get(job_id)

    assert caught.value.context == {"job_id": str(job_id)}


@pytest.mark.asyncio
async def test_list_scopes_non_admin_to_owned_jobs() -> None:
    owner_id = uuid4()
    jobs = AsyncMock(spec=JobRepository)
    jobs.list.return_value = [make_job(owner_id=owner_id)]
    jobs.count.return_value = 1
    service = build_service(jobs, AsyncMock(spec=AuditRepository), RecordingDispatcher())

    page = await service.list(
        requester_id=owner_id,
        role=UserRole.OPERATOR,
        status=None,
        job_type=None,
        limit=25,
        offset=0,
    )

    assert page.total == 1
    assert page.items[0].owner_id == owner_id
    jobs.list.assert_awaited_once_with(
        owner_id=owner_id,
        status=None,
        job_type=None,
        limit=25,
        offset=0,
    )


@pytest.mark.asyncio
async def test_cancel_marks_job_finished_and_audits_actor() -> None:
    actor_id = uuid4()
    job = make_job(status=JobStatus.RUNNING)
    jobs = AsyncMock(spec=JobRepository)
    audits = AsyncMock(spec=AuditRepository)
    jobs.get.return_value = job
    service = build_service(jobs, audits, RecordingDispatcher())

    cancelled = await service.cancel(job.id, actor_id)

    assert cancelled.status == JobStatus.CANCELLED
    assert cancelled.finished_at is not None
    audits.record.assert_awaited_once()
    jobs.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_rejects_terminal_job() -> None:
    job = make_job(status=JobStatus.SUCCEEDED)
    jobs = AsyncMock(spec=JobRepository)
    jobs.get.return_value = job
    service = build_service(jobs, AsyncMock(spec=AuditRepository), RecordingDispatcher())

    with pytest.raises(InvalidTransitionError):
        await service.cancel(job.id, uuid4())
