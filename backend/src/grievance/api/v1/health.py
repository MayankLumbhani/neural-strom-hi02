"""Health and readiness endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from grievance.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Report that the API process is alive."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
def get_readiness(request: Request) -> ReadinessResponse | JSONResponse:
    """Report database and classifier readiness."""
    if request.app.state.classifier is None:
        response = ReadinessResponse(
            status="not_ready",
            db="unknown",
            model="unavailable",
            model_error=request.app.state.classifier_error,
        )
        return JSONResponse(status_code=503, content=response.model_dump())
    return ReadinessResponse(status="ready", db="unknown", model="ready")
