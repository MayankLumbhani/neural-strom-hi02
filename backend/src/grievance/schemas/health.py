"""Health and readiness response schemas."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness response."""

    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    """Readiness response including classifier initialization status."""

    status: Literal["ready", "not_ready"]
    db: Literal["unknown"]
    model: Literal["ready", "unavailable"]
    model_error: str | None = None
