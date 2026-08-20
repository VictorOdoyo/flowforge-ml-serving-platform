from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from flowforge.models.enums import ModelStatus


class ModelVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_model_versions_name_version"),)

    name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    artifact_uri: Mapped[str] = mapped_column(String(1000), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus, name="model_status", native_enum=False),
        default=ModelStatus.DRAFT,
        index=True,
        nullable=False,
    )
    model_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
