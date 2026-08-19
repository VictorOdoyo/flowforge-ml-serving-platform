from collections.abc import Callable
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from flowforge.api.dependencies import (
    enforce_rate_limit,
    get_model_registry_service,
    require_admin,
    require_operator,
)
from flowforge.main import create_app
from flowforge.models.enums import ModelStatus, UserRole
from flowforge.models.model_version import ModelVersion
from flowforge.models.user import User
from flowforge.schemas.model_version import ModelVersionCreate


def make_model(created_by: UUID) -> ModelVersion:
    model = ModelVersion(
        name="churn-risk",
        version="2026.08.1",
        artifact_uri="s3://flowforge-models/churn-risk/model.onnx",
        checksum="a" * 64,
        status=ModelStatus.DRAFT,
        model_metadata={"framework": "onnx"},
        created_by=created_by,
    )
    model.id = uuid4()
    return model


class StubModelRegistryService:
    def __init__(self, model: ModelVersion) -> None:
        self.model = model

    async def register(self, data: ModelVersionCreate, actor_id: UUID) -> ModelVersion:
        assert data.name == self.model.name
        assert actor_id == self.model.created_by
        return self.model

    async def list(self, *, limit: int, offset: int) -> list[ModelVersion]:
        assert limit == 10
        assert offset == 0
        return [self.model]

    async def change_status(self, model_id: UUID, target: ModelStatus) -> ModelVersion:
        assert model_id == self.model.id
        self.model.status = target
        return self.model


def models_app(user: User, service: StubModelRegistryService) -> FastAPI:
    app = create_app()
    app.dependency_overrides[require_operator] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_model_registry_service] = lambda: service
    app.dependency_overrides[enforce_rate_limit] = lambda: None
    return app


def test_registers_model_version(user_factory: Callable[..., User]) -> None:
    user = user_factory(role=UserRole.OPERATOR)
    service = StubModelRegistryService(make_model(user.id))

    with TestClient(models_app(user, service)) as client:
        response = client.post(
            "/api/v1/models",
            json={
                "name": "churn-risk",
                "version": "2026.08.1",
                "artifact_uri": "s3://flowforge-models/churn-risk/model.onnx",
                "checksum": "a" * 64,
                "model_metadata": {"framework": "onnx"},
            },
        )

    assert response.status_code == 201
    assert response.json()["status"] == "draft"


def test_lists_registered_models(user_factory: Callable[..., User]) -> None:
    user = user_factory(role=UserRole.OPERATOR)
    service = StubModelRegistryService(make_model(user.id))

    with TestClient(models_app(user, service)) as client:
        response = client.get("/api/v1/models?limit=10&offset=0")

    assert response.status_code == 200
    assert response.json()[0]["name"] == "churn-risk"


def test_admin_activates_model_version(user_factory: Callable[..., User]) -> None:
    user = user_factory(role=UserRole.ADMIN)
    service = StubModelRegistryService(make_model(user.id))

    with TestClient(models_app(user, service)) as client:
        response = client.patch(
            f"/api/v1/models/{service.model.id}/status",
            json={"status": "active"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "active"
