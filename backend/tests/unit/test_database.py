"""Tests for request-scoped database session transaction handling."""

from collections.abc import Generator

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from grievance.core import database
from grievance.models import Department


def _sqlite_engine():
    """Create an isolated in-memory SQLite engine with the schema applied."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def test_get_session_commits_successful_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """Persist rows added by a successful request after its session closes."""
    engine = _sqlite_engine()
    monkeypatch.setattr(database, "get_engine", lambda settings=None: engine)

    def request() -> Generator[Session, None, None]:
        yield from database.get_session()

    generator = request()
    session = next(generator)
    session.add(
        Department(
            code="WATER",
            name_en="Water Supply",
            name_hi="जल आपूर्ति",
            name_gu="જળ પુરવઠો",
            sla_hours=48,
        )
    )
    with pytest.raises(StopIteration):
        next(generator)

    with Session(engine) as check_session:
        assert check_session.exec(select(Department)).one().code == "WATER"
    engine.dispose()


def test_get_session_rolls_back_failed_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """Discard rows added by a request that raises an exception."""
    engine = _sqlite_engine()
    monkeypatch.setattr(database, "get_engine", lambda settings=None: engine)

    generator = database.get_session()
    session = next(generator)
    session.add(
        Department(
            code="ROADS",
            name_en="Roads",
            name_hi="सड़कें",
            name_gu="રસ્તાઓ",
            sla_hours=48,
        )
    )
    with pytest.raises(RuntimeError):
        generator.throw(RuntimeError("request failed"))

    with Session(engine) as check_session:
        assert check_session.exec(select(Department)).all() == []
    engine.dispose()
