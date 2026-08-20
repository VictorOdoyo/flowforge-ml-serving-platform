# Task Bank

These are realistic future tasks that can be implemented without changing the project identity.

## API Tasks

- Add cursor pagination for audit events.
- Add operator-only job cancellation with state-machine validation.
- Add model-version rollback endpoints.
- Add output download authorization checks.

## Worker Tasks

- Add a dead-letter table for terminal worker failures.
- Add per-job concurrency keys so conflicting jobs cannot run together.
- Add retry backoff metrics.
- Add resumable report generation stages.

## Data Tasks

- Add partial indexes for active jobs by priority and status.
- Add retention policies for completed job outputs.
- Add audit-event pagination and filtering tests.
- Add migration checks that detect model enum drift.

## Deployment Tasks

- Add Helm chart values for staging and production.
- Add container vulnerability scanning.
- Add Kubernetes readiness tests in CI.
- Add release tagging documentation.

## Documentation Tasks

- Add example API requests.
- Add architecture diagrams.
- Add troubleshooting examples for Redis and PostgreSQL outages.
- Add performance tuning notes for workers.
