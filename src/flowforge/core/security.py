import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt

from flowforge.core.config import Settings
from flowforge.core.exceptions import AuthenticationError
from flowforge.models.enums import UserRole

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=64
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode()
    encoded_digest = base64.urlsafe_b64encode(digest).decode()
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${encoded_salt}${encoded_digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt_value, digest_value = encoded.split("$", maxsplit=5)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_value)
        expected = base64.urlsafe_b64decode(digest_value)
        candidate = hashlib.scrypt(
            password.encode(), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


def create_access_token(
    *, user_id: UUID, role: UserRole, settings: Settings, now: datetime | None = None
) -> tuple[str, int]:
    issued_at = now or datetime.now(UTC)
    expires_delta = timedelta(minutes=settings.access_token_minutes)
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.value,
        "iat": issued_at,
        "exp": issued_at + expires_delta,
        "iss": settings.app_name,
        "aud": "flowforge-api",
    }
    token = jwt.encode(
        claims, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            audience="flowforge-api",
            issuer=settings.app_name,
        )
    except jwt.PyJWTError as error:
        raise AuthenticationError("Access token is invalid or expired") from error
