from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from flowforge.core.exceptions import ConflictError, ResourceNotFoundError
from flowforge.models.enums import ModelStatus
from flowforge.models.model_version import ModelVersion
from flowforge.repositories.model_version import ModelVersionRepository
from flowforge.schemas.model_version import ModelVersionCreate
from flowforge.services.model_registry import ModelRegistryService


def model_version(*, status: ModelStatus = ModelStatus.DRAFT) -> ModelVersion:
    model = ModelVersion(
        name="churn-risk",
        version="2026.08.1",
        artifact_uri="s3://flowforge-models/churn-risk/2026.08.1/model.onnx",
        checksum="a" * 64,
        status=status,
        model_metadata={"framework": "onnx"},
        created_by=uuid4(),
    )
    model.id = uuid4()
    return model


@pytest.mark.asyncio
async def test_registers_model_version() -> None:
    repository_mock = AsyncMock(spec=ModelVersionRepository)
    repository_mock.add.side_effect = lambda model: model
    service = ModelRegistryService(cast(ModelVersionRepository, repository_mock))
    actor_id = uuid4()
    request = ModelVersionCreate(
        name="churn-risk",
        version="2026.08.1",
        artifact_uri="s3://flowforge-models/churn-risk/model.onnx",
        checksum="a" * 64,
        model_metadata={"framework": "onnx"},
    )

    created = await service.register(request, actor_id)

    assert created.name == request.name
    assert created.created_by == actor_id
    repository_mock.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_activates_draft_model() -> None:
    model = model_version()
    repository_mock = AsyncMock(spec=ModelVersionRepository)
    repository_mock.get.return_value = model
    service = ModelRegistryService(cast(ModelVersionRepository, repository_mock))

    updated = await service.change_status(model.id, ModelStatus.ACTIVE)

    assert updated.status == ModelStatus.ACTIVE
    repository_mock.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_rejects_reactivating_retired_model() -> None:
    model = model_version(status=ModelStatus.RETIRED)
    repository_mock = AsyncMock(spec=ModelVersionRepository)
    repository_mock.get.return_value = model
    service = ModelRegistryService(cast(ModelVersionRepository, repository_mock))

    with pytest.raises(ConflictError, match="cannot be reactivated"):
        await service.change_status(model.id, ModelStatus.ACTIVE)


@pytest.mark.asyncio
async def test_reports_missing_model() -> None:
    repository_mock = AsyncMock(spec=ModelVersionRepository)
    repository_mock.get.return_value = None
    service = ModelRegistryService(cast(ModelVersionRepository, repository_mock))

    with pytest.raises(ResourceNotFoundError, match="not found"):
        await service.change_status(uuid4(), ModelStatus.ACTIVE)
