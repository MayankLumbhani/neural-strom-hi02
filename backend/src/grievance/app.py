"""FastAPI application factory."""

from fastapi import FastAPI

from grievance.api.v1.health import router as health_router


def create_app() -> FastAPI:
    """Create the grievance API application."""
    app = FastAPI(title="Neural Storm Grievance API")
    app.include_router(health_router)
    return app
