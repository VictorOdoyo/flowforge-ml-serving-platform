# FlowForge ML Serving Platform

FlowForge is a production-oriented FastAPI platform for receiving, scheduling, and tracking
data-processing and machine-learning workloads through versioned REST APIs.

The project demonstrates an application layer, persistence layer, worker system, migration workflow,
container setup, Kubernetes manifests, and automated quality checks. It uses local seedable data and
development services so it can be run and reviewed without private credentials or external APIs.

## Features

- Versioned REST API under `/api/v1`
- JWT authentication and role-based authorization
- Durable job submission with idempotency keys
- PostgreSQL schema for users, jobs, stages, model versions, outputs, audit events, and idempotency
- Redis-backed rate limiting and Celery coordination
- Celery workers for long-running workflow execution
- Structured request IDs and error responses
- Health, readiness, and Prometheus metrics endpoints
- Alembic migrations with offline SQL validation
- Docker Compose stack for local integration
- Kubernetes manifests with probes, limits, autoscaling, disruption budgets, and network policies
- GitHub Actions for linting, formatting, typing, tests, migration validation, Compose validation, and image builds

## Tech Stack

- Python 3.12 or 3.13
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Celery
- pytest
- Ruff
- mypy
- Docker
- Kubernetes
- GitHub Actions

## Local Quick Start

Install dependencies:

```bash
uv sync
```

Start PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

Run migrations:

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run flowforge-api
```

Open `http://localhost:8000/docs`.

## Full Stack

```bash
docker compose up --build
```

The Nginx gateway exposes the API at `http://localhost:8080`.

## Quality Checks

PowerShell:

```powershell
.\scripts\check.ps1
```

Bash:

```bash
./scripts/check.sh
```

Individual checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov=flowforge --cov-report=term-missing
uv run alembic upgrade head --sql
docker compose config --quiet
kubectl kustomize deploy/k8s
```

## Project Structure

```text
src/flowforge/
  api/            FastAPI routers, dependencies, errors, and metrics
  core/           Configuration, security, logging, Redis, and exceptions
  db/             SQLAlchemy sessions and health checks
  middleware/     Request IDs, request-size limits, and metrics
  models/         SQLAlchemy persistence models
  repositories/   Database access boundaries
  schemas/        Pydantic request and response contracts
  services/       Auth, jobs, model registry, readiness, rate limits, and state transitions
  tasks/          Celery app, workflows, pipelines, and maintenance tasks
tests/            Unit and integration test suite
alembic/          Database migration environment and revisions
deploy/           Docker, Nginx, and Kubernetes deployment assets
scripts/          Local smoke, bootstrap, and quality scripts
docs/             Architecture, operations, security, and deployment guides
```

## Documentation

- [Architecture](docs/architecture.md)
- [Local development](docs/local-development.md)
- [API workflows](docs/api-workflows.md)
- [Failure recovery](docs/failure-recovery.md)
- [Deployment](docs/deployment.md)
- [Security](docs/security.md)
- [Operations](docs/operations.md)
- [Task bank](docs/task-bank.md)

## Public Safety

This repository contains no private client data, no live cloud credentials, and no production
secrets. Example configuration values are local-development defaults only.

## License

MIT
