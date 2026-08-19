import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from flowforge.core.exceptions import DomainError

logger = structlog.get_logger()


async def domain_error_handler(request: Request, error: DomainError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    await logger.awarning(
        "domain_error",
        code=error.code,
        status_code=error.status_code,
        path=request.url.path,
    )
    return JSONResponse(
        {
            "error": {
                "code": error.code,
                "message": error.message,
                "request_id": request_id,
                "context": error.context,
            }
        },
        status_code=error.status_code,
        headers=error.headers,
    )
