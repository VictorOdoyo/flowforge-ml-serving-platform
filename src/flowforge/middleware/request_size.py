from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = {key.lower(): value for key, value in scope.get("headers", [])}
            raw_length = headers.get(b"content-length")
            if raw_length is not None:
                try:
                    content_length = int(raw_length)
                except ValueError:
                    content_length = self.max_bytes + 1
                if content_length > self.max_bytes:
                    response = JSONResponse(
                        {
                            "error": {
                                "code": "request_too_large",
                                "message": "Request body is too large",
                            }
                        },
                        status_code=413,
                    )
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)
