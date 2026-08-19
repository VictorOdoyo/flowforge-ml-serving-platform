import hashlib
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.config import Settings, get_settings
from flowforge.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitExceededError,
)
from flowforge.core.redis import get_redis, redis_client
from flowforge.core.security import decode_access_token
from flowforge.db.session import engine, get_session
from flowforge.models.enums import UserRole
from flowforge.models.user import User
from flowforge.repositories.audit import AuditRepository
from flowforge.repositories.idempotency import IdempotencyRepository
from flowforge.repositories.job import JobRepository
from flowforge.repositories.model_version import ModelVersionRepository
from flowforge.repositories.user import UserRepository
from flowforge.services.auth import AuthenticationService
from flowforge.services.idempotency import IdempotencyService
from flowforge.services.job import JobService
from flowforge.services.model_registry import ModelRegistryService
from flowforge.services.rate_limit import FixedWindowRateLimiter
from flowforge.services.readiness import ReadinessService
from flowforge.tasks.dispatcher import CeleryJobDispatcher

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Bearer token is required")
    claims = decode_access_token(credentials.credentials, settings)
    user = await UserRepository(session).get_by_id(claims["sub"])
    if user is None or not user.is_active:
        raise AuthenticationError("Token subject is not an active user")
    return user


async def require_operator(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role not in {UserRole.ADMIN, UserRole.OPERATOR}:
        raise AuthorizationError("Operator access is required")
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise AuthorizationError("Administrator access is required")
    return user


async def get_job_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncIterator[JobService]:
    yield JobService(
        jobs=JobRepository(session),
        audits=AuditRepository(session),
        dispatcher=CeleryJobDispatcher(),
    )


async def get_authentication_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIterator[AuthenticationService]:
    yield AuthenticationService(UserRepository(session), settings)


async def get_idempotency_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncIterator[IdempotencyService]:
    yield IdempotencyService(IdempotencyRepository(session))


def get_readiness_service() -> ReadinessService:
    return ReadinessService(engine, redis_client)


async def get_model_registry_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncIterator[ModelRegistryService]:
    yield ModelRegistryService(ModelVersionRepository(session))


async def enforce_rate_limit(
    request: Request,
    response: Response,
    redis: Annotated[Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    authorization = request.headers.get("Authorization")
    remote = request.client.host if request.client else "unknown"
    identity_source = authorization or remote
    identity = hashlib.sha256(identity_source.encode()).hexdigest()[:24]
    limiter = FixedWindowRateLimiter(redis, limit=settings.rate_limit_per_minute)
    allowed, remaining = await limiter.allow(identity)
    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    if not allowed:
        raise RateLimitExceededError(
            "Request rate limit exceeded",
            context={"retry_after_seconds": 60},
            headers={"Retry-After": "60"},
        )
