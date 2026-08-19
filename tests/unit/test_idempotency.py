from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from flowforge.core.exceptions import ConflictError
from flowforge.models.idempotency import IdempotencyRecord
from flowforge.repositories.idempotency import IdempotencyRepository
from flowforge.services.idempotency import IdempotencyService, request_fingerprint


def make_record(payload: dict[str, object], resource_id: UUID) -> IdempotencyRecord:
    return IdempotencyRecord(
        scope="jobs:user-1",
        key="request-1",
        request_hash=request_fingerprint(payload),
        resource_id=resource_id,
        response_status=202,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


def test_request_fingerprint_is_stable_across_key_order() -> None:
    first = {"model": "churn", "inputs": {"b": 2, "a": 1}}
    second = {"inputs": {"a": 1, "b": 2}, "model": "churn"}

    assert request_fingerprint(first) == request_fingerprint(second)


@pytest.mark.asyncio
async def test_check_returns_none_for_unused_key() -> None:
    repository_mock = AsyncMock(spec=IdempotencyRepository)
    repository_mock.get.return_value = None
    service = IdempotencyService(cast(IdempotencyRepository, repository_mock))

    result = await service.check(scope="jobs:user-1", key="new-key", payload={"name": "job"})

    assert result is None


@pytest.mark.asyncio
async def test_check_replays_matching_request() -> None:
    resource_id = uuid4()
    payload = {"name": "daily scoring", "priority": 70}
    repository_mock = AsyncMock(spec=IdempotencyRepository)
    repository_mock.get.return_value = make_record(payload, resource_id)
    service = IdempotencyService(cast(IdempotencyRepository, repository_mock))

    result = await service.check(scope="jobs:user-1", key="request-1", payload=payload)

    assert result == resource_id


@pytest.mark.asyncio
async def test_check_rejects_key_reuse_with_different_payload() -> None:
    repository_mock = AsyncMock(spec=IdempotencyRepository)
    repository_mock.get.return_value = make_record({"name": "first"}, uuid4())
    service = IdempotencyService(cast(IdempotencyRepository, repository_mock))

    with pytest.raises(ConflictError, match="different request"):
        await service.check(scope="jobs:user-1", key="request-1", payload={"name": "second"})


@pytest.mark.asyncio
async def test_reserve_persists_request_fingerprint() -> None:
    resource_id = uuid4()
    repository_mock = AsyncMock(spec=IdempotencyRepository)
    repository_mock.add.side_effect = lambda record: record
    service = IdempotencyService(cast(IdempotencyRepository, repository_mock))

    record = await service.reserve(
        scope="jobs:user-1",
        key="request-1",
        payload={"name": "daily scoring"},
        resource_id=resource_id,
    )

    assert record.resource_id == resource_id
    assert record.response_status == 202
    repository_mock.add.assert_awaited_once_with(record)
    repository_mock.commit.assert_awaited_once()
