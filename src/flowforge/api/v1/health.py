from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from flowforge import __version__
from flowforge.api.dependencies import get_readiness_service
from flowforge.core.config import get_settings
from flowforge.schemas.health import HealthResponse, ReadinessCheck
from flowforge.services.readiness import ReadinessService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        service=settings.app_name,
        version=__version__,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessCheck)
async def readiness(
    response: Response,
    service: Annotated[ReadinessService, Depends(get_readiness_service)],
) -> ReadinessCheck:
    checks = await service.checks()
    ready = all(checks.values())
    response.status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessCheck(status="ready" if ready else "not_ready", checks=checks)
