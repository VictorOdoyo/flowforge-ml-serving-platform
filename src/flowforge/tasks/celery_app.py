from celery import Celery

from flowforge.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "flowforge",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["flowforge.tasks.workflows", "flowforge.tasks.maintenance"],
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_soft_time_limit=840,
    task_time_limit=900,
    result_expires=3600,
    timezone="UTC",
    task_routes={
        "flowforge.execute_job": {"queue": "workflows"},
        "flowforge.cleanup_idempotency": {"queue": "maintenance"},
    },
    beat_schedule={
        "cleanup-expired-idempotency-records": {
            "task": "flowforge.cleanup_idempotency",
            "schedule": 3600.0,
        }
    },
)
