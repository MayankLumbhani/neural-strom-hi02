"""HTTP integration tests for public chat and ticket status endpoints."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from grievance.app import create_app
from grievance.core.config import Settings
from grievance.core.database import get_session
from grievance.models import Conversation, Department, TicketEvent
from grievance.nlp.classifier import FakeClassifier
from grievance.seed import DEPARTMENTS
from grievance.services.ticket_service import TicketService


@pytest.fixture
def public_api() -> Generator[tuple[TestClient, Engine], None, None]:
    """Provide an isolated API and SQLite database with seeded departments."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                Department(
                    code=seed.code,
                    name_en=seed.name_en,
                    name_hi=seed.name_hi,
                    name_gu=seed.name_gu,
                    sla_hours=seed.sla_hours,
                )
                for seed in DEPARTMENTS
            ]
        )
        session.commit()

    def override_session() -> Generator[Session, None, None]:
        """Use the isolated test database and commit successful requests."""
        with Session(engine) as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise
            else:
                session.commit()

    settings = Settings(
        _env_file=None,
        app_env="test",
        cors_origins="https://citizen.example",
        max_message_length=80,
    )
    app = create_app(settings, classifier=FakeClassifier("WATER"))
    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, engine
    app.dependency_overrides.clear()
    engine.dispose()


def test_post_chat_message_creates_ticket(public_api: tuple[TestClient, Engine]) -> None:
    """Expose the persisted chat happy path through the public endpoint."""
    client, _ = public_api

    response = client.post(
        "/api/v1/chat/messages",
        json={"text": "Water leaks near Lotus Park for two days."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "TICKET_CREATED"
    assert body["language"] == "en"
    assert body["ticket"]["department"] == "Water Supply"
    assert body["ticket"]["ticket_id"].startswith("FMC-")


def test_chat_endpoint_persists_missing_location_follow_up(
    public_api: tuple[TestClient, Engine],
) -> None:
    """Use a conversation ID to continue a request that needs location."""
    client, _ = public_api
    first = client.post("/api/v1/chat/messages", json={"text": "Water supply stopped."})
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        "/api/v1/chat/messages",
        json={"text": "Ward 8", "conversation_id": conversation_id},
    )

    assert first.json()["state"] == "AWAITING_LOCATION"
    assert second.status_code == 200
    assert second.json()["state"] == "TICKET_CREATED"
    assert second.json()["ticket"]["ticket_id"].startswith("FMC-")


def test_public_ticket_lookup_returns_only_public_fields(
    public_api: tuple[TestClient, Engine],
) -> None:
    """Keep complaint and contact data out of the public status response."""
    client, engine = public_api
    with Session(engine) as session:
        department = session.exec(select(Department).where(Department.code == "WATER")).one()
        conversation = Conversation(language="en")
        session.add(conversation)
        session.flush()
        ticket = TicketService(session, Settings(_env_file=None)).create_ticket(
            conversation_id=conversation.id,
            department_id=department.id,
            complaint_text="private synthetic complaint",
            language="en",
            location_text="Ward 2",
            contact_phone="5550101234",
        )
        session.add(
            TicketEvent(
                ticket_id=ticket.id,
                from_status="FILED",
                to_status="ASSIGNED",
                actor_type="officer",
                note="internal synthetic note",
                is_public=False,
            )
        )
        session.commit()
        public_id = ticket.public_id

    response = client.get(f"/api/v1/tickets/{public_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["public_id"] == public_id
    assert body["status"] == "Filed"
    assert body["department"] == "Water Supply"
    assert body["location"] == "Ward 2"
    assert len(body["public_events"]) == 1
    assert "private synthetic complaint" not in response.text
    assert "5550101234" not in response.text
    assert "internal synthetic note" not in response.text


def test_public_ticket_lookup_uses_standard_not_found_error(
    public_api: tuple[TestClient, Engine],
) -> None:
    """Return a consistent 404 error for missing public ticket IDs."""
    client, _ = public_api

    response = client.get("/api/v1/tickets/FMC-261102-MISS")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TICKET_NOT_FOUND"


def test_chat_request_validates_size_and_extra_fields(
    public_api: tuple[TestClient, Engine],
) -> None:
    """Reject oversized messages and unexpected request fields."""
    client, _ = public_api

    oversized = client.post("/api/v1/chat/messages", json={"text": "x" * 81})
    extra_field = client.post(
        "/api/v1/chat/messages",
        json={"text": "hello", "phone": "5550101234"},
    )

    assert oversized.status_code == 413
    assert oversized.json()["error"]["code"] == "MESSAGE_TOO_LONG"
    assert extra_field.status_code == 422
    assert extra_field.json()["error"]["code"] == "VALIDATION_ERROR"


def test_configured_cors_allows_the_frontend_origin(
    public_api: tuple[TestClient, Engine],
) -> None:
    """Apply configured frontend origins to browser preflight requests."""
    client, _ = public_api

    response = client.options(
        "/api/v1/chat/messages",
        headers={
            "Origin": "https://citizen.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://citizen.example"


def test_chat_request_schema_rejects_empty_text(
    public_api: tuple[TestClient, Engine],
) -> None:
    """Reject a blank request body through the standard validation response."""
    client, _ = public_api

    response = client.post("/api/v1/chat/messages", json={"text": ""})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
