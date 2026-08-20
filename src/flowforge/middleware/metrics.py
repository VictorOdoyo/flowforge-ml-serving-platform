from time import perf_counter

from prometheus_client import Counter, Histogram
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HTTP_REQUESTS = Counter(
    "flowforge_http_requests_total",
    "Total HTTP requests",
    labelnames=("method", "route", "status"),
)
HTTP_DURATION = Histogram(
    "flowforge_http_request_duration_seconds",
    "HTTP request duration",
    labelnames=("method", "route"),
)


class MetricsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = perf_counter()
        status_code = 500

        async def capture_status(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, capture_status)
        finally:
            route = scope.get("route")
            route_path = getattr(route, "path", scope.get("path", "unknown"))
            method = scope.get("method", "unknown")
            HTTP_REQUESTS.labels(method=method, route=route_path, status=str(status_code)).inc()
            HTTP_DURATION.labels(method=method, route=route_path).observe(perf_counter() - started)
