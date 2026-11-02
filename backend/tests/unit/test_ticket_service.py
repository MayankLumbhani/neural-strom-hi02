"""Tests for ticket creation, identifiers, status transitions, and events."""

import re
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from grievance.core.config import Settings
from grievance.core.exceptions import DomainError
from grievance.models import Conversation, Department, Ticket, TicketEvent
from grievance.services.ticket_service import TicketService, generate_public_id

STATUSES = ("FILED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "ESCALATED")
EXPECTED_TRANSITIONS = {
    "FILED": {"ASSIGNED", "ESCALATED"},
    "ASSIGNED": {"IN_PROGRESS", "ESCALATED"},
    "IN_PROGRESS": {"RESOLVED", "ESCALATED"},
    "RESOLVED": set(),
    "ESCALATED": {"IN_PROGRESS", "RESOLVED"},
}


@pytest.fixture
def ticket_database() -> Iterator[tuple[Session, Department, Conversation]]:
    """Create an isolated SQLite session with a department and conversation."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    department = Department(
        code="WATER",
        name_en="Water Supply",
        name_hi="जल आपूर्ति",
        name_gu="પાણી પુરવઠો",
        sla_hours=24,
    )
    conversation = Conversation(language="en")
    session.add(department)
    session.add(conversation)
    session.flush()
    yield session, department, conversation
    session.close()
    engine.dispose()


def test_public_id_format_uses_configured_prefix_and_utc_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Produce the documented prefix-date-four-character public ID."""
    monkeypatch.setattr("grievance.services.ticket_service.secrets.choice", lambda _: "A")

    public_id = generate_public_id("CITY", datetime(2026, 11, 2, tzinfo=UTC))

    assert public_id == "CITY-261102-AAAA"
    assert re.fullmatch(r"[A-Z0-9]+-\d{6}-[A-Z0-9]{4}", public_id)


def test_create_ticket_retries_public_id_collisions_and_records_creation_event(
    ticket_database: tuple[Session, Department, Conversation],
) -> None:
    """Retry an occupied public ID and persist the initial FILED event."""
    session, department, conversation = ticket_database
    existing = Ticket(
        public_id="FMC-261102-DUP1",
        conversation_id=conversation.id,
        department_id=department.id,
        complaint_text="Existing synthetic ticket",
        language="en",
        location_text="Ward 1",
    )
    session.add(existing)
    session.flush()
    second_conversation = Conversation(language="gu")
    session.add(second_conversation)
    session.flush()
    generated_ids = iter(("FMC-261102-DUP1", "FMC-261102-NEW1"))
    service = TicketService(
        session,
        Settings(_env_file=None, ticket_id_prefix="FMC"),
        public_id_generator=lambda _: next(generated_ids),
    )

    ticket = service.create_ticket(
        conversation_id=second_conversation.id,
        department_id=department.id,
        complaint_text="Water supply is interrupted",
        language="gu",
        location_text="Ward 2",
        predicted_confidence=0.9,
    )
    events = session.exec(select(TicketEvent).where(TicketEvent.ticket_id == ticket.id)).all()

    assert ticket.public_id == "FMC-261102-NEW1"
    assert ticket.status == "FILED"
    assert len(events) == 1
    assert events[0].from_status is None
    assert events[0].to_status == "FILED"
    assert events[0].actor_type == "citizen"
    assert events[0].is_public


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [(source, target) for source in STATUSES for target in STATUSES],
)
def test_status_transition_matrix(
    ticket_database: tuple[Session, Department, Conversation],
    from_status: str,
    to_status: str,
) -> None:
    """Allow only the documented lifecycle transitions and record valid changes."""
    session, department, conversation = ticket_database
    ticket = Ticket(
        public_id="FMC-261102-TEST",
        conversation_id=conversation.id,
        department_id=department.id,
        complaint_text="Synthetic complaint",
        language="en",
        location_text="Ward 1",
        status=from_status,
    )
    session.add(ticket)
    session.flush()
    session.add(
        TicketEvent(
            ticket_id=ticket.id,
            from_status=None,
            to_status=from_status,
            actor_type="citizen",
        )
    )
    session.flush()
    service = TicketService(session, Settings(_env_file=None))
    should_transition = to_status in EXPECTED_TRANSITIONS[from_status]

    if should_transition:
        result = service.transition_status(
            ticket.public_id,
            to_status,
            actor_type="officer",
            note="Synthetic status update",
            is_public=True,
        )
        assert result.status == to_status
        if to_status == "RESOLVED":
            assert result.resolved_at is not None
    else:
        with pytest.raises(DomainError) as error:
            service.transition_status(ticket.public_id, to_status, actor_type="officer")
        assert error.value.code == "INVALID_TRANSITION"
        assert error.value.status_code == 409

    events = session.exec(select(TicketEvent).where(TicketEvent.ticket_id == ticket.id)).all()
    assert len(events) == (2 if should_transition else 1)


def test_transition_status_reports_missing_ticket(
    ticket_database: tuple[Session, Department, Conversation],
) -> None:
    """Return a domain 404 when a ticket public ID is unknown."""
    session, _, _ = ticket_database
    service = TicketService(session, Settings(_env_file=None))

    with pytest.raises(DomainError) as error:
        service.transition_status("FMC-261102-MISS", "ASSIGNED", actor_type="officer")

    assert error.value.code == "TICKET_NOT_FOUND"
    assert error.value.status_code == 404
