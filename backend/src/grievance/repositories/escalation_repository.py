"""Atomic persistence operations for overdue ticket escalation."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, or_, update
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, select

from grievance.models import Department, Ticket, TicketEvent

ACTIVE_TICKET_STATUSES = ("FILED", "ASSIGNED", "IN_PROGRESS")


def escalate_overdue_tickets(
    session: Session,
    now: datetime,
    demo_mode: bool,
) -> int:
    """Escalate overdue tickets once and record events in the caller's transaction."""
    department_rows = session.exec(select(Department.id, Department.sla_hours)).all()
    overdue_conditions: list[ColumnElement[bool]] = []
    for department_id, sla_hours in department_rows:
        if department_id is None:
            continue
        sla_window = timedelta(minutes=sla_hours) if demo_mode else timedelta(hours=sla_hours)
        overdue_conditions.append(
            and_(
                col(Ticket.department_id) == department_id,
                col(Ticket.status_changed_at) < now - sla_window,
            )
        )
    if not overdue_conditions:
        return 0

    overdue_filter = or_(*overdue_conditions)
    eligible_filter = col(Ticket.status).in_(ACTIVE_TICKET_STATUSES)
    candidates = session.exec(
        select(col(Ticket.id), col(Ticket.status)).where(eligible_filter, overdue_filter)
    ).all()
    if not candidates:
        return 0

    previous_statuses: dict[UUID, str] = {ticket_id: status for ticket_id, status in candidates}
    updated_result = session.exec(
        update(Ticket)
        .where(
            col(Ticket.id).in_(previous_statuses),
            eligible_filter,
            overdue_filter,
        )
        .values(
            status="ESCALATED",
            escalation_level=col(Ticket.escalation_level) + 1,
            status_changed_at=now,
        )
        .returning(col(Ticket.id))
    )
    updated_ids = updated_result.scalars().all()
    session.add_all(
        [
            TicketEvent(
                ticket_id=ticket_id,
                from_status=previous_statuses[ticket_id],
                to_status="ESCALATED",
                actor_type="system",
            )
            for ticket_id in updated_ids
        ]
    )
    session.flush()
    return len(updated_ids)
