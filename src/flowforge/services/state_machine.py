from flowforge.core.exceptions import InvalidTransitionError
from flowforge.models.enums import JobStatus

ALLOWED_JOB_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.QUEUED: frozenset({JobStatus.RUNNING, JobStatus.CANCELLED, JobStatus.FAILED}),
    JobStatus.RUNNING: frozenset(
        {JobStatus.RETRYING, JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}
    ),
    JobStatus.RETRYING: frozenset({JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.FAILED}),
    JobStatus.SUCCEEDED: frozenset(),
    JobStatus.FAILED: frozenset(),
    JobStatus.CANCELLED: frozenset(),
}


def ensure_job_transition(current: JobStatus, target: JobStatus) -> None:
    if target == current:
        return
    if target not in ALLOWED_JOB_TRANSITIONS[current]:
        raise InvalidTransitionError(
            f"Cannot transition job from {current.value} to {target.value}",
            context={"current": current.value, "target": target.value},
        )
