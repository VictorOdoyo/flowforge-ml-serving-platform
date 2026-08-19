from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str
    environment: str


class ReadinessCheck(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, bool]

