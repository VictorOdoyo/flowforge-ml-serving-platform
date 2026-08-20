from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from flowforge.models.enums import JobStatus, JobType


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("priority BETWEEN 0 AND 100", name="priority_range"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="progress_range"),
        Index("ix_jobs_owner_status_created", "owner_id", "status", "created_at"),
        Index("ix_jobs_status_queued", "status", "queued_at"),
    )

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    model_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type", native_enum=False), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", native_enum=False),
        default=JobStatus.QUEUED,
        index=True,
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
