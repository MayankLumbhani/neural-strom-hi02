"""HTTP middleware for request IDs and privacy-safe access logs."""

from time import perf_counter
from uuid import UUID, uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from grievance.core.exceptions import handle_unexpected_error
from grievance.core.logging import logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request IDs and log request metadata without request content."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Set a validated request ID, return it in the response, and log metadata."""
        request_id = _get_request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            response = await handle_unexpected_error(request, exc)
            response.headers["X-Request-ID"] = request_id
            status_code = response.status_code
            return response
        finally:
            logger.info(
                "request.completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round((perf_counter() - started) * 1000, 3),
                },
            )


def _get_request_id(header_value: str | None) -> str:
    """Accept UUID request IDs and replace absent or invalid values."""
    if header_value is not None:
        try:
            return str(UUID(header_value))
        except ValueError:
            return str(uuid4())
    return str(uuid4())
