from fastapi import FastAPI
from fastapi.testclient import TestClient

from flowforge.api.dependencies import enforce_rate_limit, get_authentication_service
from flowforge.main import create_app
from flowforge.schemas.auth import LoginRequest, TokenResponse


class StubAuthenticationService:
    async def login(self, credentials: LoginRequest) -> TokenResponse:
        assert credentials.email == "operator@example.com"
        return TokenResponse(access_token="signed-test-token", expires_in=900)


def authenticated_app() -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_authentication_service] = StubAuthenticationService
    app.dependency_overrides[enforce_rate_limit] = lambda: None
    return app


def test_token_endpoint_returns_bearer_contract() -> None:
    with TestClient(authenticated_app()) as client:
        response = client.post(
            "/api/v1/auth/token",
            json={
                "email": "operator@example.com",
                "password": "valid-password",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "signed-test-token",
        "token_type": "bearer",
        "expires_in": 900,
    }


def test_token_endpoint_validates_credentials_shape() -> None:
    with TestClient(authenticated_app()) as client:
        response = client.post(
            "/api/v1/auth/token",
            json={"email": "not-an-email", "password": "short"},
        )

    assert response.status_code == 422
    fields = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", "email") in fields
    assert ("body", "password") in fields
