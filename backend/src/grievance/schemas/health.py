"""Health and readiness response schemas."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness response."""

    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    """Readiness response before database and model checks are implemented."""

    status: Literal["ready"]
    db: Literal["unknown"]
    model: Literal["unknown"]
