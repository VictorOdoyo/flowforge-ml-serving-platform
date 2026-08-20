# Contributing

FlowForge uses small, focused changes with tests and documentation updates when behavior changes.

## Local Setup

```bash
uv sync
docker compose up -d postgres redis
uv run alembic upgrade head
```

## Before Opening a Pull Request

Run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov=flowforge --cov-report=term-missing
uv run alembic upgrade head --sql
docker compose config --quiet
kubectl kustomize deploy/k8s
```

## Commit Style

Prefer conventional prefixes such as:

- `feat:`
- `fix:`
- `test:`
- `docs:`
- `deploy:`
- `ci:`
- `chore:`

Keep each commit tied to one clear outcome.
