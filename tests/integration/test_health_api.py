from fastapi import FastAPI
from fastapi.testclient import TestClient

from flowforge.api.dependencies import get_readiness_service
from flowforge.main import create_app


class StubReadinessService:
    def __init__(self, checks: dict[str, bool]) -> None:
        self.result = checks

    async def checks(self) -> dict[str, bool]:
        return self.result


def readiness_app(checks: dict[str, bool]) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_readiness_service] = lambda: StubReadinessService(checks)
    return app


def test_health_endpoint_exposes_service_identity() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health", headers={"X-Request-ID": "health-check-1"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "FlowForge ML Serving Platform",
        "version": "0.1.0",
        "environment": "local",
    }
    assert response.headers["X-Request-ID"] == "health-check-1"


def test_readiness_endpoint_reports_api_check() -> None:
    checks = {"api": True, "database": True, "redis": True}
    with TestClient(readiness_app(checks)) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": checks}


def test_readiness_endpoint_fails_when_dependency_is_down() -> None:
    checks = {"api": True, "database": True, "redis": False}
    with TestClient(readiness_app(checks)) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": checks}


def test_metrics_endpoint_uses_prometheus_format() -> None:
    with TestClient(create_app()) as client:
        client.get("/api/v1/health")
        response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "flowforge_http_requests_total" in response.text
