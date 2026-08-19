from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IdempotencyRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("scope", "key", name="uq_idempotency_records_scope_key"),
        Index("ix_idempotency_records_expires", "expires_at"),
    )

    scope: Mapped[str] = mapped_column(String(160), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID | None]
    response_status: Mapped[int | None] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

