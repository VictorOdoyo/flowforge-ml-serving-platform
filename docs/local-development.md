# Local Development

## Prerequisites

- Python 3.12 or 3.13
- uv
- Docker Desktop
- Docker Compose
- kubectl for manifest validation

## Install

```bash
uv sync
```

## Start Datastores

```bash
docker compose up -d postgres redis
```

## Run Migrations

```bash
uv run alembic upgrade head
```

## Start the API

```bash
uv run flowforge-api
```

The API is available at `http://localhost:8000`.

## Start the Full Stack

```bash
docker compose up --build
```

The Nginx gateway exposes the API at `http://localhost:8080`.

## Smoke Test

```bash
uv run python scripts/smoke_test.py
```

Set `FLOWFORGE_BASE_URL=http://localhost:8080` when testing through the gateway.

## Local Quality Gates

On PowerShell:

```powershell
.\scripts\check.ps1
```

On bash:

```bash
./scripts/check.sh
```
