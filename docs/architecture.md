# Architecture

FlowForge is organized around a durable job ledger and asynchronous workers.

## Runtime Components

- FastAPI exposes versioned REST APIs under `/api/v1`.
- PostgreSQL stores users, jobs, stages, model versions, outputs, audit events, and idempotency records.
- Redis supports short-lived rate limiting, Celery brokering, and task result coordination.
- Celery workers execute long-running data preparation, inference, report generation, and file processing work.
- Alembic owns database schema changes.
- Prometheus metrics expose request and worker-facing operational signals.

## Request Lifecycle

1. A client authenticates with JWT credentials.
2. The API validates payload size, request shape, roles, and rate limits.
3. Job creation runs inside a transaction and checks an optional idempotency key.
4. The job is persisted with queued status and stage metadata.
5. Celery receives the durable work item and processes it outside the HTTP request path.
6. The client polls job state and output links through read APIs.

## Code Organization

- `api/` contains routers, dependencies, error contracts, and metrics.
- `core/` contains configuration, logging, security, Redis, and exception primitives.
- `db/` owns SQLAlchemy engine/session setup and datastore health checks.
- `models/` contains persistence entities.
- `repositories/` contains database access boundaries.
- `schemas/` contains Pydantic request and response contracts.
- `services/` contains business rules such as state transitions, auth, idempotency, and rate limiting.
- `tasks/` contains Celery app configuration and workflow execution.

## Design Principles

- Keep API handlers thin and service-focused.
- Store workflow state before dispatching expensive work.
- Make client retries safe through idempotency records.
- Keep user-facing errors structured and stable.
- Prefer explicit state transitions over free-form status mutation.
- Make local development possible without private cloud credentials.
