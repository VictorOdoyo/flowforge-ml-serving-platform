from uuid import UUID

from flowforge.services.dispatcher import DispatchReceipt
from flowforge.tasks.celery_app import celery_app


class CeleryJobDispatcher:
    def enqueue(self, job_id: UUID) -> DispatchReceipt:
        result = celery_app.send_task("flowforge.execute_job", args=[str(job_id)])
        return DispatchReceipt(task_id=result.id)

