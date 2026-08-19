from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from flowforge.models.enums import ModelStatus


class ModelVersionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    version: str = Field(min_length=1, max_length=80)
    artifact_uri: str = Field(min_length=5, max_length=1000)
    checksum: str = Field(min_length=32, max_length=128)
    model_metadata: dict[str, Any] = Field(default_factory=dict)


class ModelVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    version: str
    artifact_uri: str
    checksum: str
    status: ModelStatus
    model_metadata: dict[str, Any]
    created_by: UUID


class ModelStatusUpdate(BaseModel):
    status: ModelStatus

