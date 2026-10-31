"""Domain exceptions and their HTTP response handlers."""

from collections.abc import Mapping
from typing import cast
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from grievance.core.logging import logger
from grievance.schemas.errors import ErrorDetail, ErrorResponse


class DomainError(Exception):
    """An expected business error with an HTTP status and stable error code."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: Mapping[str, object] | None = None,
    ) -> None:
        """Create a domain error with a response-safe details mapping."""
        if not 400 <= status_code < 600:
            raise ValueError("Domain error status_code must be between 400 and 599")
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = dict(details or {})


def register_exception_handlers(app: FastAPI) -> None:
    """Register consistent error responses for API and domain exceptions."""
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)


def _request_id(request: Request) -> str:
    """Read the request ID assigned by middleware, with a safe fallback."""
    request_id = getattr(request.state, "request_id", None)
    return str(request_id or uuid4())


def _error_response(
    request: Request,
    status_code: int,
    error: ErrorDetail,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build the standard typed error response."""
    response = ErrorResponse(error=error, request_id=_request_id(request))
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
        headers=dict(headers or {}),
    )


async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
    """Map a domain error to its declared status and standard response."""
    error = cast(DomainError, exc)
    return _error_response(
        request,
        error.status_code,
        ErrorDetail(code=error.code, message=error.message, details=error.details),
    )


async def handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    """Map framework HTTP errors to the standard response format."""
    error = cast(StarletteHTTPException, exc)
    message = error.detail if isinstance(error.detail, str) else "Request failed"
    return _error_response(
        request,
        error.status_code,
        ErrorDetail(
            code=f"HTTP_{error.status_code}",
            message=message,
            details={},
        ),
        error.headers,
    )


async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    """Return validation locations and types without echoing submitted values."""
    error = cast(RequestValidationError, exc)
    validation_errors = [
        {
            "field": ".".join(str(part) for part in item["loc"]),
            "type": item["type"],
        }
        for item in error.errors()
    ]
    return _error_response(
        request,
        422,
        ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": validation_errors},
        ),
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Log an unexpected exception without its potentially sensitive message."""
    logger.error(
        "request.unhandled_exception",
        extra={"request_id": _request_id(request), "error_type": type(exc).__name__},
    )
    return _error_response(
        request,
        500,
        ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={},
        ),
    )
