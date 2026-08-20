Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov=flowforge --cov-report=term-missing
uv run alembic upgrade head --sql | Out-Null
docker compose config --quiet
kubectl kustomize deploy/k8s | Out-Null
