from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from flowforge.models.enums import OutputKind


class JobOutputRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    kind: OutputKind
    uri: str | None
    payload: dict[str, Any] | None
    checksum: str | None
    content_type: str

