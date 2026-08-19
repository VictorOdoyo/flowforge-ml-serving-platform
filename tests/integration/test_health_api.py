from fastapi.testclient import TestClient

from flowforge.main import create_app


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
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"api": True}}


def test_metrics_endpoint_uses_prometheus_format() -> None:
    with TestClient(create_app()) as client:
        client.get("/api/v1/health")
        response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "flowforge_http_requests_total" in response.text
