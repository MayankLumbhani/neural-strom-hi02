"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from grievance.api.v1.chat import router as chat_router
from grievance.api.v1.health import router as health_router
from grievance.api.v1.tickets import router as tickets_router
from grievance.core.config import Settings, get_settings
from grievance.core.exceptions import register_exception_handlers
from grievance.core.logging import configure_logging, logger
from grievance.core.middleware import RequestContextMiddleware
from grievance.nlp.classifier import Classifier, ClassifierLoadError, build_classifier


def create_app(
    settings: Settings | None = None,
    classifier: Classifier | None = None,
) -> FastAPI:
    """Create the grievance API application."""
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        """Load the selected classifier once as the application starts."""
        try:
            application.state.classifier = (
                classifier if classifier is not None else build_classifier(resolved_settings)
            )
            application.state.classifier_error = None
        except ClassifierLoadError as error:
            application.state.classifier = None
            application.state.classifier_error = str(error)
            logger.error(
                "classifier.initialization.failed backend=%s reason=%s",
                resolved_settings.classifier_backend,
                error,
            )
        yield

    app = FastAPI(title="Neural Storm Grievance API", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.classifier = None
    app.state.classifier_error = None
    app.include_router(chat_router)
    app.include_router(health_router)
    app.include_router(tickets_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    return app
