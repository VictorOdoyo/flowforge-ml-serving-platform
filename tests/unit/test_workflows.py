from flowforge.models.enums import JobStatus
from flowforge.tasks.workflows import MAX_JOB_ATTEMPTS, classify_failure


def test_retryable_failure_returns_retrying_when_attempts_remain() -> None:
    assert classify_failure(TimeoutError("temporary"), MAX_JOB_ATTEMPTS - 1) == JobStatus.RETRYING


def test_retryable_failure_returns_failed_after_last_attempt() -> None:
    assert classify_failure(OSError("network"), MAX_JOB_ATTEMPTS) == JobStatus.FAILED


def test_non_retryable_failure_returns_failed_immediately() -> None:
    assert classify_failure(ValueError("bad payload"), 1) == JobStatus.FAILED
