from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    job_id: UUID | None
    action: str
    resource_type: str
    resource_id: str
    detail: dict[str, Any]
    source_ip: str | None
    request_id: str | None
    created_at: datetime

