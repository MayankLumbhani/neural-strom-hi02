"""SQLModel engine and request-scoped session dependency."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from grievance.core.config import Settings, get_settings


@lru_cache
def _create_engine(database_url: str) -> Engine:
    """Create and cache an engine for a database URL."""
    return create_engine(database_url, pool_pre_ping=True)


def get_engine(settings: Settings | None = None) -> Engine:
    """Return the configured database engine or raise when no URL is configured."""
    resolved_settings = settings or get_settings()
    if resolved_settings.database_url is None:
        raise RuntimeError("DATABASE_URL must be configured before opening a database session")
    return _create_engine(resolved_settings.database_url.get_secret_value())


def get_session() -> Generator[Session, None, None]:
    """Yield a request-scoped database session and close it after the request."""
    with Session(get_engine()) as session:
        yield session
