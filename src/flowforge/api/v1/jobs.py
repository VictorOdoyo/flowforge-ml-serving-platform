from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.api.dependencies import (
    enforce_rate_limit,
    get_current_user,
    get_idempotency_service,
    get_job_service,
    require_operator,
)
from flowforge.core.exceptions import AuthorizationError
from flowforge.db.session import get_session
from flowforge.models.enums import JobStatus, JobType, UserRole
from flowforge.models.user import User
from flowforge.repositories.audit import AuditRepository
from flowforge.repositories.output import OutputRepository
from flowforge.repositories.stage import StageRepository
from flowforge.schemas.audit import AuditEventRead
from flowforge.schemas.common import Page
from flowforge.schemas.job import JobCancelResponse, JobCreate, JobRead
from flowforge.schemas.output import JobOutputRead
from flowforge.schemas.stage import StageRead
from flowforge.services.idempotency import IdempotencyService
from flowforge.services.job import JobService

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(enforce_rate_limit)],
)


def ensure_job_access(job: JobRead, user: User) -> None:
    if user.role != UserRole.ADMIN and job.owner_id != user.id:
        raise AuthorizationError("You do not have access to this job")


@router.post("", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
async def submit_job(
    data: JobCreate,
    service: Annotated[JobService, Depends(get_job_service)],
    idempotency: Annotated[IdempotencyService, Depends(get_idempotency_service)],
    user: Annotated[User, Depends(require_operator)],
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", min_length=8, max_length=255),
    ] = None,
) -> JobRead:
    payload = data.model_dump(mode="json")
    scope = f"jobs:{user.id}"
    if idempotency_key:
        existing_id = await idempotency.check(
            scope=scope,
            key=idempotency_key,
            payload=payload,
        )
        if existing_id is not None:
            return JobRead.model_validate(await service.get(existing_id))

    job = await service.submit(user.id, data)
    if idempotency_key:
        await idempotency.reserve(
            scope=scope,
            key=idempotency_key,
            payload=payload,
            resource_id=job.id,
        )
    return JobRead.model_validate(job)


@router.get("", response_model=Page[JobRead])
async def list_jobs(
    service: Annotated[JobService, Depends(get_job_service)],
    user: Annotated[User, Depends(get_current_user)],
    job_status: Annotated[JobStatus | None, Query(alias="status")] = None,
    job_type: JobType | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[JobRead]:
    return await service.list(
        requester_id=user.id,
        role=user.role,
        status=job_status,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID,
    service: Annotated[JobService, Depends(get_job_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> JobRead:
    result = JobRead.model_validate(await service.get(job_id))
    ensure_job_access(result, user)
    return result


@router.post("/{job_id}/cancel", response_model=JobCancelResponse)
async def cancel_job(
    job_id: UUID,
    service: Annotated[JobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_operator)],
) -> JobCancelResponse:
    current = JobRead.model_validate(await service.get(job_id))
    ensure_job_access(current, user)
    cancelled = await service.cancel(job_id, user.id)
    return JobCancelResponse(id=cancelled.id, status=cancelled.status, cancelled=True)


@router.get("/{job_id}/stages", response_model=list[StageRead])
async def list_job_stages(
    job_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[JobService, Depends(get_job_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[StageRead]:
    job = JobRead.model_validate(await service.get(job_id))
    ensure_job_access(job, user)
    rows = await StageRepository(session).list_for_job(job_id)
    return [StageRead.model_validate(row) for row in rows]


@router.get("/{job_id}/outputs", response_model=list[JobOutputRead])
async def list_job_outputs(
    job_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[JobService, Depends(get_job_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[JobOutputRead]:
    job = JobRead.model_validate(await service.get(job_id))
    ensure_job_access(job, user)
    rows = await OutputRepository(session).list_for_job(job_id)
    return [JobOutputRead.model_validate(row) for row in rows]


@router.get("/{job_id}/events", response_model=list[AuditEventRead])
async def list_job_events(
    job_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[JobService, Depends(get_job_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[AuditEventRead]:
    job = JobRead.model_validate(await service.get(job_id))
    ensure_job_access(job, user)
    rows = await AuditRepository(session).list_for_job(job_id)
    return [AuditEventRead.model_validate(row) for row in rows]
