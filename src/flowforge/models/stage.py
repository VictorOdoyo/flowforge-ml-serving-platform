from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from flowforge.models.enums import StageStatus


class ProcessingStage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "processing_stages"
    __table_args__ = (
        UniqueConstraint("job_id", "sequence", name="uq_processing_stages_job_sequence"),
        Index("ix_processing_stages_job_status", "job_id", "status"),
    )

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StageStatus] = mapped_column(
        Enum(StageStatus, name="stage_status", native_enum=False),
        default=StageStatus.PENDING,
        nullable=False,
    )
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
