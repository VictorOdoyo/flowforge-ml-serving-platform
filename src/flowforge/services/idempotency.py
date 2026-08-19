import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from flowforge.core.exceptions import ConflictError
from flowforge.models.idempotency import IdempotencyRecord
from flowforge.repositories.idempotency import IdempotencyRepository


def request_fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


class IdempotencyService:
    def __init__(self, records: IdempotencyRepository) -> None:
        self.records = records

    async def check(self, *, scope: str, key: str, payload: dict[str, Any]) -> UUID | None:
        existing = await self.records.get(scope, key)
        if existing is None:
            return None
        if existing.request_hash != request_fingerprint(payload):
            raise ConflictError(
                "Idempotency key was already used with a different request",
                context={"scope": scope},
            )
        return existing.resource_id

    async def reserve(
        self,
        *,
        scope: str,
        key: str,
        payload: dict[str, Any],
        resource_id: UUID,
        ttl_hours: int = 24,
    ) -> IdempotencyRecord:
        record = IdempotencyRecord(
            scope=scope,
            key=key,
            request_hash=request_fingerprint(payload),
            resource_id=resource_id,
            response_status=202,
            expires_at=datetime.now(UTC) + timedelta(hours=ttl_hours),
        )
        await self.records.add(record)
        await self.records.commit()
        return record
