"""Ticket and ticket-event persistence operations."""

from uuid import UUID

from sqlalchemy import true
from sqlmodel import Session, select

from grievance.models import Ticket, TicketEvent


def get_ticket_by_public_id(session: Session, public_id: str) -> Ticket | None:
    """Find a ticket by its public identifier."""
    return session.exec(select(Ticket).where(Ticket.public_id == public_id)).one_or_none()


def get_ticket_for_conversation(session: Session, conversation_id: UUID) -> Ticket | None:
    """Find the ticket created from a conversation, if one exists."""
    return session.exec(
        select(Ticket).where(Ticket.conversation_id == conversation_id)
    ).one_or_none()


def list_public_ticket_events(session: Session, ticket_id: UUID) -> list[TicketEvent]:
    """Return only explicitly public events for a ticket in chronological order."""
    events = session.exec(
        select(TicketEvent).where(
            TicketEvent.ticket_id == ticket_id,
            TicketEvent.is_public == true(),
        )
    ).all()
    return sorted(events, key=lambda event: (event.created_at, str(event.id)))


def create_ticket(session: Session, ticket: Ticket) -> Ticket:
    """Add and flush a new ticket."""
    session.add(ticket)
    session.flush()
    return ticket


def update_ticket(session: Session, ticket: Ticket) -> Ticket:
    """Flush changes to a ticket already loaded in the current session."""
    session.add(ticket)
    session.flush()
    return ticket


def add_ticket_event(session: Session, event: TicketEvent) -> TicketEvent:
    """Add and flush an auditable ticket event."""
    session.add(event)
    session.flush()
    return event
