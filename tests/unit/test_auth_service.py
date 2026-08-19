from collections.abc import Callable
from typing import cast
from unittest.mock import AsyncMock

import pytest

from flowforge.core.config import Settings
from flowforge.core.exceptions import AuthenticationError
from flowforge.core.security import decode_access_token, hash_password
from flowforge.models.enums import UserRole
from flowforge.models.user import User
from flowforge.repositories.user import UserRepository
from flowforge.schemas.auth import LoginRequest
from flowforge.services.auth import AuthenticationService


@pytest.mark.asyncio
async def test_login_returns_signed_access_token(
    settings: Settings,
    user_factory: Callable[..., User],
) -> None:
    user = user_factory(
        role=UserRole.OPERATOR,
        hashed_password=hash_password("very-secure-password"),
    )
    repository_mock = AsyncMock(spec=UserRepository)
    repository_mock.get_by_email.return_value = user
    service = AuthenticationService(cast(UserRepository, repository_mock), settings)

    response = await service.login(
        LoginRequest(email="operator@example.com", password="very-secure-password")
    )

    claims = decode_access_token(response.access_token, settings)
    assert claims["sub"] == str(user.id)
    assert response.token_type == "bearer"


@pytest.mark.asyncio
@pytest.mark.parametrize("is_active", [True, False])
async def test_login_rejects_invalid_credentials(
    is_active: bool,
    settings: Settings,
    user_factory: Callable[..., User],
) -> None:
    user = user_factory(
        is_active=is_active,
        hashed_password=hash_password("correct-password"),
    )
    repository_mock = AsyncMock(spec=UserRepository)
    repository_mock.get_by_email.return_value = user
    service = AuthenticationService(cast(UserRepository, repository_mock), settings)

    with pytest.raises(AuthenticationError, match="incorrect"):
        await service.login(
            LoginRequest(email="operator@example.com", password="incorrect-password")
        )


@pytest.mark.asyncio
async def test_login_does_not_reveal_unknown_email(settings: Settings) -> None:
    repository_mock = AsyncMock(spec=UserRepository)
    repository_mock.get_by_email.return_value = None
    service = AuthenticationService(cast(UserRepository, repository_mock), settings)

    with pytest.raises(AuthenticationError, match="Email or password is incorrect"):
        await service.login(
            LoginRequest(email="missing@example.com", password="some-long-password")
        )
