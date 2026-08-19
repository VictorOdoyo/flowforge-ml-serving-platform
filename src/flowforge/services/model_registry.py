from uuid import UUID

from flowforge.core.exceptions import ConflictError, ResourceNotFoundError
from flowforge.models.enums import ModelStatus
from flowforge.models.model_version import ModelVersion
from flowforge.repositories.model_version import ModelVersionRepository
from flowforge.schemas.model_version import ModelVersionCreate


class ModelRegistryService:
    def __init__(self, models: ModelVersionRepository) -> None:
        self.models = models

    async def register(self, data: ModelVersionCreate, actor_id: UUID) -> ModelVersion:
        model = ModelVersion(created_by=actor_id, **data.model_dump())
        await self.models.add(model)
        await self.models.commit()
        return model

    async def change_status(self, model_id: UUID, target: ModelStatus) -> ModelVersion:
        model = await self.models.get(model_id)
        if model is None:
            raise ResourceNotFoundError(
                "Model version was not found", context={"model_id": str(model_id)}
            )
        if model.status == ModelStatus.RETIRED and target != ModelStatus.RETIRED:
            raise ConflictError("A retired model version cannot be reactivated")
        model.status = target
        await self.models.commit()
        return model

