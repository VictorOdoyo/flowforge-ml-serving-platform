# Failure Recovery

FlowForge assumes distributed work can fail because of timeouts, worker restarts, duplicate client
submissions, dependency outages, or invalid model inputs.

## Recovery Controls

- Idempotency records prevent duplicate job creation after client retries.
- Job status transitions are validated by a state machine.
- Retryable worker errors are marked separately from terminal failures.
- Readiness checks cover PostgreSQL and Redis before traffic reaches the API.
- Audit events record important workflow and model-version changes.

## Operational Playbook

1. Check `/api/v1/ready` to confirm datastore connectivity.
2. Check `/metrics` for request rates, errors, and latency.
3. Inspect jobs stuck in queued or retrying states.
4. Review audit events for model activations and job-state transitions.
5. Restart workers only after verifying PostgreSQL and Redis are reachable.

## Data Safety

The API persists job records before dispatching Celery work. If a worker exits during execution, the
job remains visible and can be retried or marked failed by operational tooling.
