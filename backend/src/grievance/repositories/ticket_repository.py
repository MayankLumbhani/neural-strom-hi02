"""Ticket and ticket-event persistence operations."""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import func, or_, true
from sqlmodel import Session, col, select

from grievance.models import Department, Ticket, TicketEvent


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


def list_tickets(
    session: Session,
    department_id: int | None,
    status: str | None,
    department_code: str | None,
    search: str | None,
    date_from: date | None,
    date_to: date | None,
    offset: int,
    limit: int,
) -> tuple[list[tuple[Ticket, Department]], int]:
    """Return a filtered ticket page and total count within the department scope."""
    ticket_department_id = col(Ticket.department_id)
    department_primary_key = col(Department.id)
    ticket_status = col(Ticket.status)
    department_code_column = col(Department.code)
    ticket_created_at = col(Ticket.created_at)
    statement = select(Ticket, Department).join(
        Department,
        ticket_department_id == department_primary_key,
    )
    count_statement = select(func.count(col(Ticket.id))).join(
        Department,
        ticket_department_id == department_primary_key,
    )
    if department_id is not None:
        statement = statement.where(ticket_department_id == department_id)
        count_statement = count_statement.where(ticket_department_id == department_id)
    if status is not None:
        statement = statement.where(ticket_status == status)
        count_statement = count_statement.where(ticket_status == status)
    if department_code is not None:
        statement = statement.where(department_code_column == department_code)
        count_statement = count_statement.where(department_code_column == department_code)
    if search is not None:
        pattern = f"%{search}%"
        search_filter = or_(
            col(Ticket.public_id).ilike(pattern),
            col(Ticket.complaint_text).ilike(pattern),
            col(Ticket.location_text).ilike(pattern),
        )
        statement = statement.where(search_filter)
        count_statement = count_statement.where(search_filter)
    if date_from is not None:
        start = datetime.combine(date_from, time.min, tzinfo=UTC)
        statement = statement.where(ticket_created_at >= start)
        count_statement = count_statement.where(ticket_created_at >= start)
    if date_to is not None:
        end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
        statement = statement.where(ticket_created_at < end)
        count_statement = count_statement.where(ticket_created_at < end)

    total = int(session.exec(count_statement).one())
    items = session.exec(
        statement.order_by(col(Ticket.created_at).desc(), col(Ticket.public_id))
        .offset(offset)
        .limit(limit)
    ).all()
    return list(items), total


def get_scoped_ticket(
    session: Session,
    public_id: str,
    department_id: int | None,
) -> tuple[Ticket, Department] | None:
    """Find a ticket only when it belongs to the supplied department scope."""
    statement = (
        select(Ticket, Department)
        .join(
            Department,
            col(Ticket.department_id) == col(Department.id),
        )
        .where(col(Ticket.public_id) == public_id)
    )
    if department_id is not None:
        statement = statement.where(col(Ticket.department_id) == department_id)
    result = session.exec(statement).one_or_none()
    return result


def list_ticket_events(session: Session, ticket_id: UUID) -> list[TicketEvent]:
    """Return the complete event history for a ticket in chronological order."""
    events = session.exec(select(TicketEvent).where(TicketEvent.ticket_id == ticket_id)).all()
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
