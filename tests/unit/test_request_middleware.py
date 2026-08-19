from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from flowforge.middleware.request_id import RequestIDMiddleware
from flowforge.middleware.request_size import RequestSizeLimitMiddleware


async def echo(request: Request) -> JSONResponse:
    return JSONResponse({"size": len(await request.body())})


def build_client(*, max_bytes: int = 32) -> TestClient:
    app = Starlette(routes=[Route("/echo", echo, methods=["POST"])])
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=max_bytes)
    app.add_middleware(RequestIDMiddleware)
    return TestClient(app)


def test_generates_request_id_when_header_is_absent() -> None:
    response = build_client().post("/echo", content=b"small")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_preserves_caller_request_id() -> None:
    response = build_client().post(
        "/echo",
        content=b"small",
        headers={"X-Request-ID": "trace-2026-08-19"},
    )

    assert response.headers["X-Request-ID"] == "trace-2026-08-19"


def test_rejects_declared_body_larger_than_limit() -> None:
    response = build_client(max_bytes=4).post("/echo", content=b"12345")

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "request_too_large"


def test_accepts_body_at_size_limit() -> None:
    response = build_client(max_bytes=5).post("/echo", content=b"12345")

    assert response.status_code == 200
    assert response.json() == {"size": 5}
