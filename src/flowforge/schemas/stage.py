from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from flowforge.models.enums import StageStatus


class StageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    name: str
    sequence: int
    status: StageStatus
    detail: dict[str, Any]
    started_at: datetime | None
    finished_at: datetime | None

