from uuid import uuid4

import pytest
from pydantic import SecretStr

from flowforge.core.config import Settings
from flowforge.core.exceptions import AuthenticationError
from flowforge.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from flowforge.models.enums import UserRole


def test_password_hash_round_trip() -> None:
    encoded = hash_password("correct horse battery staple")

    assert encoded.startswith("scrypt$")
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("incorrect password", encoded)


@pytest.mark.parametrize("encoded", ["", "plain-text", "scrypt$broken", "argon2$1$2$3$4$5"])
def test_password_verification_rejects_malformed_hashes(encoded: str) -> None:
    assert not verify_password("irrelevant", encoded)


def test_access_token_round_trip(settings: Settings) -> None:
    user_id = uuid4()
    token, expires_in = create_access_token(
        user_id=user_id,
        role=UserRole.OPERATOR,
        settings=settings,
    )

    claims = decode_access_token(token, settings)

    assert claims["sub"] == str(user_id)
    assert claims["role"] == UserRole.OPERATOR.value
    assert expires_in == 900


def test_access_token_rejects_wrong_secret(settings: Settings) -> None:
    token, _ = create_access_token(
        user_id=uuid4(),
        role=UserRole.VIEWER,
        settings=settings,
    )
    other_settings = settings.model_copy(
        update={"jwt_secret": SecretStr("a-different-signing-secret")}
    )

    with pytest.raises(AuthenticationError, match="invalid or expired"):
        decode_access_token(token, other_settings)
