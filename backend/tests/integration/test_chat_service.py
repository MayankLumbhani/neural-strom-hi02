"""Integration tests for the persisted chat flow using deterministic classifiers."""

from collections.abc import Iterator
from uuid import UUID

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from grievance.core.config import Settings
from grievance.core.exceptions import DomainError
from grievance.models import Conversation, Department, Ticket, TicketEvent
from grievance.nlp.classifier import FakeClassifier
from grievance.repositories.conversation_repository import list_messages
from grievance.seed import DEPARTMENTS
from grievance.services.chat_service import ChatService
from grievance.services.ticket_service import TicketService


@pytest.fixture
def chat_database() -> Iterator[Session]:
    """Create an isolated database populated with the nine synthetic departments."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
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
    session.flush()
    yield session
    session.close()
    engine.dispose()


def _service(session: Session, label: str, confidence: float = 1.0) -> ChatService:
    """Build chat orchestration with a deterministic offline classifier."""
    return ChatService(
        session,
        Settings(_env_file=None, llm_enabled=False),
        FakeClassifier(label, confidence),
    )


def test_happy_path_files_ticket_and_persists_conversation(
    chat_database: Session,
) -> None:
    """Classify a complaint, extract its location, and create a ticket."""
    response = _service(chat_database, "WATER").handle_message(
        "Water leaks near Lotus Park for two days."
    )

    ticket = chat_database.exec(select(Ticket)).one()
    events = chat_database.exec(select(TicketEvent)).all()
    messages = list_messages(chat_database, response.conversation_id)

    assert response.state == "TICKET_CREATED"
    assert response.language == "en"
    assert response.ticket is not None
    assert response.ticket.ticket_id == ticket.public_id
    assert response.ticket.department == "Water Supply"
    assert ticket.location_text == "Lotus Park"
    assert ticket.status == "FILED"
    assert events[0].to_status == "FILED"
    assert [message.sender for message in messages] == ["citizen", "bot"]


def test_missing_location_waits_for_citizen_then_files_ticket(
    chat_database: Session,
) -> None:
    """Retain complaint and department while requesting a missing location."""
    service = _service(chat_database, "WATER")
    first = service.handle_message("Water supply stopped.")

    assert first.state == "AWAITING_LOCATION"
    assert first.ticket is None

    second = service.handle_message("Ward 7", first.conversation_id)

    ticket = chat_database.exec(select(Ticket)).one()
    assert second.state == "TICKET_CREATED"
    assert second.ticket is not None
    assert ticket.complaint_text == "Water supply stopped."
    assert ticket.location_text == "Ward 7"


def test_low_confidence_clarification_offers_all_departments_then_uses_other(
    chat_database: Session,
) -> None:
    """Offer department choices and route unresolved clarification to OTHER."""
    service = _service(chat_database, "OTHER", confidence=0.2)
    first = service.handle_message("Something is wrong.")

    assert first.state == "AWAITING_DEPARTMENT"
    assert len(first.reply.quick_replies) == 9

    second = service.handle_message("I still do not know; near Ward 2", first.conversation_id)

    ticket = chat_database.exec(select(Ticket)).one()
    assert second.state == "TICKET_CREATED"
    assert second.ticket is not None
    assert second.ticket.department == "General or Unclear"
    assert ticket.location_text == "Ward 2"


def test_medium_confidence_offers_two_ranked_departments(
    chat_database: Session,
) -> None:
    """Ask the citizen to confirm one of the model's two leading departments."""
    service = ChatService(
        chat_database,
        Settings(_env_file=None, llm_enabled=False),
        FakeClassifier("WATER", top_k=[("WATER", 0.6), ("ROADS", 0.4)]),
    )

    response = service.handle_message("Water is not available.")

    assert response.state == "AWAITING_DEPARTMENT"
    assert response.reply.quick_replies == ["Water Supply", "Roads and Infrastructure"]


def test_ticket_id_status_lookup_returns_fixed_localized_reply(
    chat_database: Session,
) -> None:
    """Look up a public ticket ID without exposing complaint text."""
    conversation = Conversation(language="en")
    chat_database.add(conversation)
    department = chat_database.exec(select(Department).where(Department.code == "WATER")).one()
    chat_database.flush()
    ticket_service = TicketService(chat_database, Settings(_env_file=None))
    ticket = ticket_service.create_ticket(
        conversation_id=conversation.id,
        department_id=department.id,
        complaint_text="Synthetic private complaint",
        language="en",
        location_text="Ward 1",
    )

    response = _service(chat_database, "OTHER").handle_message(
        ticket.public_id,
        conversation.id,
    )

    assert response.state == "IDLE"
    assert response.ticket is not None
    assert response.ticket.status == "Filed"
    assert ticket.public_id in response.reply.text
    assert "Synthetic private complaint" not in response.reply.text


@pytest.mark.parametrize("text", ["hello", "help"])
def test_greeting_and_help_use_fixed_template(
    chat_database: Session,
    text: str,
) -> None:
    """Handle exact greeting and help messages without invoking complaint logic."""
    response = _service(chat_database, "WATER").handle_message(text)

    assert response.state == "IDLE"
    assert "ticket ID" in response.reply.text
    assert chat_database.exec(select(Ticket)).all() == []


def test_unknown_conversation_id_returns_not_found(chat_database: Session) -> None:
    """Reject unknown conversation identifiers instead of creating replacement state."""
    with pytest.raises(DomainError) as error:
        _service(chat_database, "WATER").handle_message(
            "Water leaks near Lotus Park",
            UUID("00000000-0000-0000-0000-000000000001"),
        )

    assert error.value.code == "CONVERSATION_NOT_FOUND"
    assert error.value.status_code == 404


def test_chat_service_rejects_second_ticket_for_same_conversation(
    chat_database: Session,
) -> None:
    """Respect the schema's one-ticket-per-conversation constraint explicitly."""
    service = _service(chat_database, "WATER")
    first = service.handle_message("Water leaks near Lotus Park.")
    chat_database.commit()

    with pytest.raises(DomainError) as error:
        service.handle_message("Water leaks near Lotus Park again.", first.conversation_id)

    assert error.value.code == "CONVERSATION_ALREADY_HAS_TICKET"
    assert error.value.status_code == 409


def test_conversation_messages_are_persisted_in_order(chat_database: Session) -> None:
    """Persist citizen follow-up and bot messages across a multi-turn flow."""
    service = _service(chat_database, "WATER")
    first = service.handle_message("Water supply stopped.")
    service.handle_message("Ward 7", first.conversation_id)

    messages = list_messages(chat_database, first.conversation_id)

    assert [message.sender for message in messages] == ["citizen", "bot", "citizen", "bot"]
    assert messages[0].text == "Water supply stopped."
    assert messages[2].text == "Ward 7"
