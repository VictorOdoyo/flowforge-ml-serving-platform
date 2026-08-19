from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from flowforge.api.errors import domain_error_handler
from flowforge.api.metrics import router as metrics_router
from flowforge.api.v1.router import api_router
from flowforge.core.config import get_settings
from flowforge.core.exceptions import DomainError
from flowforge.core.logging import configure_logging
from flowforge.core.redis import close_redis
from flowforge.db.session import dispose_engine
from flowforge.middleware.metrics import MetricsMiddleware
from flowforge.middleware.request_id import RequestIDMiddleware
from flowforge.middleware.request_size import RequestSizeLimitMiddleware

settings = get_settings()
configure_logging(settings.log_level, json_logs=settings.environment != "local")
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await logger.ainfo("application_started", environment=settings.environment)
    yield
    await close_redis()
    await dispose_engine()
    await logger.ainfo("application_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Versioned APIs for durable workflows and model-serving jobs.",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
    )
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.max_request_bytes)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    app.include_router(metrics_router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run(
        "flowforge.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
