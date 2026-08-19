import pytest

from flowforge.core.exceptions import InvalidTransitionError
from flowforge.models.enums import JobStatus
from flowforge.services.state_machine import ALLOWED_JOB_TRANSITIONS, ensure_job_transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (current, target)
        for current, targets in ALLOWED_JOB_TRANSITIONS.items()
        for target in targets
    ],
)
def test_allows_declared_job_transitions(current: JobStatus, target: JobStatus) -> None:
    ensure_job_transition(current, target)


@pytest.mark.parametrize("status", list(JobStatus))
def test_allows_idempotent_status_updates(status: JobStatus) -> None:
    ensure_job_transition(status, status)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (JobStatus.SUCCEEDED, JobStatus.RUNNING),
        (JobStatus.FAILED, JobStatus.QUEUED),
        (JobStatus.CANCELLED, JobStatus.RUNNING),
        (JobStatus.QUEUED, JobStatus.SUCCEEDED),
    ],
)
def test_rejects_invalid_job_transitions(current: JobStatus, target: JobStatus) -> None:
    with pytest.raises(InvalidTransitionError) as caught:
        ensure_job_transition(current, target)

    assert caught.value.context == {"current": current.value, "target": target.value}
