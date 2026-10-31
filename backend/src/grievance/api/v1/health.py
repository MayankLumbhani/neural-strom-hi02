"""Health and readiness endpoints."""

from fastapi import APIRouter

from grievance.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Report that the API process is alive."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
def get_readiness() -> ReadinessResponse:
    """Report readiness while database and model checks are not yet available."""
    return ReadinessResponse(status="ready", db="unknown", model="unknown")
