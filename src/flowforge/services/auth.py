from flowforge.core.config import Settings
from flowforge.core.exceptions import AuthenticationError
from flowforge.core.security import create_access_token, verify_password
from flowforge.repositories.user import UserRepository
from flowforge.schemas.auth import LoginRequest, TokenResponse


class AuthenticationService:
    def __init__(self, users: UserRepository, settings: Settings) -> None:
        self.users = users
        self.settings = settings

    async def login(self, credentials: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(credentials.email)
        if user is None or not user.is_active:
            raise AuthenticationError("Email or password is incorrect")
        if not verify_password(credentials.password, user.hashed_password):
            raise AuthenticationError("Email or password is incorrect")
        token, expires_in = create_access_token(
            user_id=user.id, role=user.role, settings=self.settings
        )
        return TokenResponse(access_token=token, expires_in=expires_in)

