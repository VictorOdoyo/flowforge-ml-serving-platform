# FlowForge ML Serving Platform

FlowForge is a production-oriented FastAPI service for receiving, scheduling, and tracking
data-processing and machine-learning workloads through versioned REST APIs.

The platform separates responsive HTTP request handling from durable background execution.
PostgreSQL stores workflow state, Redis coordinates short-lived work, and Celery runs jobs with
retry and failure-recovery policies.

## Local quick start

```bash
uv sync
docker compose up -d postgres redis
uv run alembic upgrade head
uv run flowforge-api
```

Open `http://localhost:8000/docs` for the interactive API reference.

More detailed architecture, operations, testing, and deployment guides live in `docs/`.

