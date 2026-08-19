from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.api.dependencies import enforce_rate_limit, require_admin, require_operator
from flowforge.db.session import get_session
from flowforge.models.enums import ModelStatus
from flowforge.models.user import User
from flowforge.repositories.model_version import ModelVersionRepository
from flowforge.schemas.model_version import (
    ModelStatusUpdate,
    ModelVersionCreate,
    ModelVersionRead,
)
from flowforge.services.model_registry import ModelRegistryService

router = APIRouter(
    prefix="/models",
    tags=["model registry"],
    dependencies=[Depends(enforce_rate_limit)],
)


@router.post("", response_model=ModelVersionRead, status_code=status.HTTP_201_CREATED)
async def register_model(
    data: ModelVersionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(require_operator)],
) -> ModelVersionRead:
    service = ModelRegistryService(ModelVersionRepository(session))
    return ModelVersionRead.model_validate(await service.register(data, user.id))


@router.get("", response_model=list[ModelVersionRead])
async def list_models(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_operator)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ModelVersionRead]:
    rows = await ModelVersionRepository(session).list(limit=limit, offset=offset)
    return [ModelVersionRead.model_validate(row) for row in rows]


@router.patch("/{model_id}/status", response_model=ModelVersionRead)
async def update_model_status(
    model_id: UUID,
    data: ModelStatusUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_admin)],
) -> ModelVersionRead:
    service = ModelRegistryService(ModelVersionRepository(session))
    updated = await service.change_status(model_id, ModelStatus(data.status))
    return ModelVersionRead.model_validate(updated)
