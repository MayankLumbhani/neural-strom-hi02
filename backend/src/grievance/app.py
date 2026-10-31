"""FastAPI application factory."""

from fastapi import FastAPI

from grievance.api.v1.health import router as health_router
from grievance.core.config import Settings, get_settings
from grievance.core.exceptions import register_exception_handlers
from grievance.core.logging import configure_logging
from grievance.core.middleware import RequestContextMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the grievance API application."""
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    app = FastAPI(title="Neural Storm Grievance API")
    app.state.settings = resolved_settings
    app.include_router(health_router)
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    return app
