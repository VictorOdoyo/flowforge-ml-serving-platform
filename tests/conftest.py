from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import SecretStr

from flowforge.core.config import Settings
from flowforge.models.enums import UserRole
from flowforge.models.user import User

TEST_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
TEST_ADMIN_ID = UUID("22222222-2222-4222-8222-222222222222")


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        redis_url="redis://localhost:6379/15",
        jwt_secret=SecretStr("test-secret-that-is-more-than-32-bytes-for-hs256"),
        access_token_minutes=15,
    )


@pytest.fixture
def user_factory() -> Callable[..., User]:
    def factory(
        *,
        user_id: UUID = TEST_USER_ID,
        email: str = "operator@example.com",
        role: UserRole = UserRole.OPERATOR,
        is_active: bool = True,
        hashed_password: str | None = None,
    ) -> User:
        now = datetime.now(UTC)
        user = User(
            email=email,
            full_name="Test Operator",
            role=role,
            is_active=is_active,
            hashed_password=hashed_password or "",
        )
        user.id = user_id
        user.created_at = now
        user.updated_at = now
        return user

    return factory
