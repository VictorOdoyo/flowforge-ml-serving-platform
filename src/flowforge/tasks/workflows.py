import asyncio
from datetime import UTC, datetime
from uuid import UUID

from celery import Task
from sqlalchemy import select

from flowforge.models.enums import JobStatus, OutputKind
from flowforge.models.job import Job
from flowforge.models.output import JobOutput
from flowforge.tasks.celery_app import celery_app
from flowforge.tasks.pipelines import PIPELINES
from flowforge.db.session import session_factory


async def execute_job_async(job_id: UUID) -> None:
    async with session_factory() as session:
        statement = select(Job).where(Job.id == job_id).with_for_update()
        job = await session.scalar(statement)
        if job is None or job.status == JobStatus.CANCELLED:
            return
        job.status = JobStatus.RUNNING
        job.started_at = job.started_at or datetime.now(UTC)
        job.attempt_count += 1
        await session.commit()

        try:
            result = await PIPELINES[job.job_type].run(job.payload)
        except Exception as error:
            job.status = JobStatus.RETRYING
            job.error_code = type(error).__name__
            job.error_message = str(error)[:1000]
            await session.commit()
            raise

        session.add(
            JobOutput(
                job_id=job.id,
                kind=OutputKind.JSON,
                payload=result.payload,
                content_type=result.content_type,
            )
        )
        job.status = JobStatus.SUCCEEDED
        job.progress = 100
        job.finished_at = datetime.now(UTC)
        job.error_code = None
        job.error_message = None
        await session.commit()


@celery_app.task(
    bind=True,
    name="flowforge.execute_job",
    autoretry_for=(OSError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def execute_job(_: Task, job_id: str) -> None:
    asyncio.run(execute_job_async(UUID(job_id)))

