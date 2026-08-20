import pytest

from flowforge.models.enums import JobType
from flowforge.tasks.pipelines import PIPELINES


@pytest.mark.asyncio
async def test_data_preparation_reports_row_counts() -> None:
    result = await PIPELINES[JobType.DATA_PREPARATION].run({"row_count": 1250})

    assert result.payload == {"accepted_rows": 1250, "rejected_rows": 0}


@pytest.mark.asyncio
async def test_model_inference_returns_one_prediction_per_record() -> None:
    records = [{"account_id": "A-1"}, {"account_id": "A-2"}]

    result = await PIPELINES[JobType.MODEL_INFERENCE].run({"records": records})

    assert result.payload["predictions"] == [0.5, 0.5]
    assert result.payload["model_latency_ms"] == 12


@pytest.mark.asyncio
async def test_report_generation_uses_supplied_title() -> None:
    result = await PIPELINES[JobType.REPORT_GENERATION].run({"title": "Weekly model health"})

    assert result.payload == {"title": "Weekly model health", "sections": 1}


@pytest.mark.asyncio
async def test_file_processing_preserves_source_uri() -> None:
    source = "s3://flowforge-inputs/batch-42.csv"

    result = await PIPELINES[JobType.FILE_PROCESSING].run({"uri": source})

    assert result.payload == {"source": source, "status": "processed"}
    assert result.content_type == "application/json"
