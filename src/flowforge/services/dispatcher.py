from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DispatchReceipt:
    task_id: str


class JobDispatcher(Protocol):
    def enqueue(self, job_id: UUID) -> DispatchReceipt: ...

