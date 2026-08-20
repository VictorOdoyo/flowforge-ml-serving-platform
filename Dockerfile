# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.12.5 AS uv

FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

RUN addgroup --system flowforge \
    && adduser --system --ingroup flowforge --home /app flowforge

COPY --from=uv /uv /uvx /usr/local/bin/
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts
RUN uv sync --frozen --no-dev \
    && chown -R flowforge:flowforge /app

USER flowforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3)"]

CMD ["/app/.venv/bin/flowforge-api"]
