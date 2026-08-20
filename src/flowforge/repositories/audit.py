from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.models.audit_event import AuditEvent


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        actor_id: UUID | None = None,
        job_id: UUID | None = None,
        detail: dict[str, Any] | None = None,
        source_ip: str | None = None,
        request_id: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=actor_id,
            job_id=job_id,
            detail=detail or {},
            source_ip=source_ip,
            request_id=request_id,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_for_job(self, job_id: UUID, *, limit: int = 100) -> list[AuditEvent]:
        statement = (
            select(AuditEvent)
            .where(AuditEvent.job_id == job_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        return list((await self.session.scalars(statement)).all())
