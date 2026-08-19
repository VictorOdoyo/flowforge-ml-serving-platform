from fastapi import APIRouter, status

from flowforge import __version__
from flowforge.core.config import get_settings
from flowforge.schemas.health import HealthResponse, ReadinessCheck

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        service=settings.app_name,
        version=__version__,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessCheck, status_code=status.HTTP_200_OK)
async def readiness() -> ReadinessCheck:
    return ReadinessCheck(status="ready", checks={"api": True})

