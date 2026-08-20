from dataclasses import dataclass
from typing import Any, Protocol

from flowforge.models.enums import JobType


@dataclass(frozen=True, slots=True)
class PipelineResult:
    payload: dict[str, Any]
    content_type: str = "application/json"


class Pipeline(Protocol):
    async def run(self, payload: dict[str, Any]) -> PipelineResult: ...


class DataPreparationPipeline:
    async def run(self, payload: dict[str, Any]) -> PipelineResult:
        rows = int(payload.get("row_count", 0))
        return PipelineResult(payload={"accepted_rows": rows, "rejected_rows": 0})


class ModelInferencePipeline:
    async def run(self, payload: dict[str, Any]) -> PipelineResult:
        records = payload.get("records", [])
        return PipelineResult(
            payload={"predictions": [0.5 for _ in records], "model_latency_ms": 12}
        )


class ReportGenerationPipeline:
    async def run(self, payload: dict[str, Any]) -> PipelineResult:
        return PipelineResult(
            payload={"title": payload.get("title", "Generated report"), "sections": 1}
        )


class FileProcessingPipeline:
    async def run(self, payload: dict[str, Any]) -> PipelineResult:
        return PipelineResult(payload={"source": payload.get("uri"), "status": "processed"})


PIPELINES: dict[JobType, Pipeline] = {
    JobType.DATA_PREPARATION: DataPreparationPipeline(),
    JobType.MODEL_INFERENCE: ModelInferencePipeline(),
    JobType.REPORT_GENERATION: ReportGenerationPipeline(),
    JobType.FILE_PROCESSING: FileProcessingPipeline(),
}
