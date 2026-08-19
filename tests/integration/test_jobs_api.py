from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from flowforge.api.dependencies import (
    get_current_user,
    get_idempotency_service,
    get_job_service,
    require_operator,
)
from flowforge.main import create_app
from flowforge.models.enums import JobStatus, JobType, UserRole
from flowforge.models.job import Job
from flowforge.models.user import User
from flowforge.schemas.common import Page
from flowforge.schemas.job import JobCreate, JobRead


def make_job(owner_id: UUID) -> Job:
    now = datetime.now(UTC)
    job = Job(
        owner_id=owner_id,
        name="Daily churn scoring",
        job_type=JobType.MODEL_INFERENCE,
        status=JobStatus.QUEUED,
        payload={"records": [{"account_id": "A-1"}]},
        priority=70,
        progress=0,
        attempt_count=0,
        max_attempts=3,
        queued_at=now,
        task_id="task-42",
    )
    job.id = uuid4()
    job.created_at = now
    job.updated_at = now
    return job


class StubJobService:
    def __init__(self, job: Job) -> None:
        self.job = job

    async def submit(self, owner_id: UUID, data: JobCreate) -> Job:
        assert owner_id == self.job.owner_id
        assert data.job_type == self.job.job_type
        return self.job

    async def get(self, job_id: UUID) -> Job:
        assert job_id == self.job.id
        return self.job

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
        assert requester_id == self.job.owner_id
        assert role == UserRole.OPERATOR
        assert status is None
        assert job_type is None
        return Page[JobRead](
            items=[JobRead.model_validate(self.job)],
            total=1,
            limit=limit,
            offset=offset,
        )


class StubIdempotencyService:
    async def check(
        self,
        *,
        scope: str,
        key: str,
        payload: dict[str, object],
    ) -> UUID | None:
        return None

    async def reserve(
        self,
        *,
        scope: str,
        key: str,
        payload: dict[str, object],
        resource_id: UUID,
    ) -> None:
        return None


def jobs_app(user: User, service: StubJobService) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_operator] = lambda: user
    app.dependency_overrides[get_job_service] = lambda: service
    app.dependency_overrides[get_idempotency_service] = StubIdempotencyService
    return app


def test_submits_job_for_authenticated_operator(
    user_factory: Callable[..., User],
) -> None:
    user = user_factory()
    service = StubJobService(make_job(user.id))

    with TestClient(jobs_app(user, service)) as client:
        response = client.post(
            "/api/v1/jobs",
            json={
                "name": "Daily churn scoring",
                "job_type": "model_inference",
                "payload": {"records": [{"account_id": "A-1"}]},
                "priority": 70,
            },
            headers={"Idempotency-Key": "daily-churn-2026-08-19"},
        )

    assert response.status_code == 202
    assert response.json()["task_id"] == "task-42"
    assert response.json()["status"] == "queued"


def test_lists_jobs_with_pagination_contract(
    user_factory: Callable[..., User],
) -> None:
    user = user_factory()
    service = StubJobService(make_job(user.id))

    with TestClient(jobs_app(user, service)) as client:
        response = client.get("/api/v1/jobs?limit=10&offset=0")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["limit"] == 10
    assert len(response.json()["items"]) == 1


def test_prevents_operator_from_reading_another_users_job(
    user_factory: Callable[..., User],
) -> None:
    user = user_factory()
    service = StubJobService(make_job(uuid4()))

    with TestClient(jobs_app(user, service)) as client:
        response = client.get(f"/api/v1/jobs/{service.job.id}")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
