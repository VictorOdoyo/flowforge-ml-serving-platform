from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from flowforge.models.enums import JobStatus, JobType


class JobCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Daily churn scoring",
                "job_type": "model_inference",
                "payload": {"dataset_uri": "s3://datasets/accounts.parquet"},
                "priority": 70,
            }
        }
    )

    name: str = Field(min_length=3, max_length=180)
    job_type: JobType
    payload: dict[str, Any] = Field(default_factory=dict)
    model_version_id: UUID | None = None
    priority: int = Field(default=50, ge=0, le=100)
    max_attempts: int = Field(default=3, ge=1, le=10)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    model_version_id: UUID | None
    name: str
    job_type: JobType
    status: JobStatus
    payload: dict[str, Any]
    priority: int
    progress: int
    attempt_count: int
    max_attempts: int
    task_id: str | None
    error_code: str | None
    error_message: str | None
    queued_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class JobStatusUpdate(BaseModel):
    status: JobStatus
    progress: int | None = Field(default=None, ge=0, le=100)
    error_code: str | None = Field(default=None, max_length=80)
    error_message: str | None = Field(default=None, max_length=1000)


class JobCancelResponse(BaseModel):
    id: UUID
    status: JobStatus
    cancelled: bool
