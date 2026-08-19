from fastapi import FastAPI
from fastapi.testclient import TestClient

from flowforge.core.exceptions import ResourceNotFoundError
from flowforge.main import create_app


def error_app() -> FastAPI:
    app = create_app()

    @app.get("/missing-resource")
    async def missing_resource() -> None:
        raise ResourceNotFoundError(
            "Requested artifact was not found",
            context={"artifact_id": "artifact-42"},
        )

    return app


def test_domain_error_uses_structured_envelope() -> None:
    with TestClient(error_app()) as client:
        response = client.get(
            "/missing-resource",
            headers={"X-Request-ID": "request-error-42"},
        )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "resource_not_found",
            "message": "Requested artifact was not found",
            "request_id": "request-error-42",
            "context": {"artifact_id": "artifact-42"},
        }
    }


def test_generated_request_id_is_in_error_body_and_header() -> None:
    with TestClient(error_app()) as client:
        response = client.get("/missing-resource")

    assert response.status_code == 404
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
