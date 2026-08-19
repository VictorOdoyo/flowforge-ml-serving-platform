from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from flowforge.models.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth token type, not a credential.
    expires_in: int


class CurrentUser(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
