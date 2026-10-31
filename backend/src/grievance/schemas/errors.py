"""Standard API error response schemas."""

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Structured error information."""

    code: str
    message: str
    details: dict[str, object]


class ErrorResponse(BaseModel):
    """Standard API error response with request correlation ID."""

    error: ErrorDetail
    request_id: str
