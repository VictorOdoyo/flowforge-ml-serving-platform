from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from flowforge.models.enums import OutputKind


class JobOutput(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_outputs"

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[OutputKind] = mapped_column(
        Enum(OutputKind, name="output_kind", native_enum=False), nullable=False
    )
    uri: Mapped[str | None] = mapped_column(String(1000))
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    checksum: Mapped[str | None] = mapped_column(String(128))
    content_type: Mapped[str] = mapped_column(
        String(160), default="application/json", nullable=False
    )
