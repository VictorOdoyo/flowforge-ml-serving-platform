from typing import Annotated

from fastapi import APIRouter, Depends

from flowforge.api.dependencies import enforce_rate_limit, get_authentication_service
from flowforge.schemas.auth import LoginRequest, TokenResponse
from flowforge.services.auth import AuthenticationService

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    dependencies=[Depends(enforce_rate_limit)],
)


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    credentials: LoginRequest,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> TokenResponse:
    return await service.login(credentials)
