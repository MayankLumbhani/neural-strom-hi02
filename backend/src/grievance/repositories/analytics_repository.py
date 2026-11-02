"""Database aggregations for the authenticated analytics summary."""

from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, col, select

from grievance.models import Department, Ticket


def get_ticket_counts_by_department(
    session: Session,
    department_id: int | None,
) -> list[tuple[str, str, int]]:
    """Count tickets by department within an optional department scope."""
    statement = (
        select(
            col(Department.code),
            col(Department.name_en),
            func.count(col(Ticket.id)),
        )
        .join(Department, col(Ticket.department_id) == col(Department.id))
        .group_by(col(Department.code), col(Department.name_en))
        .order_by(col(Department.code))
    )
    if department_id is not None:
        statement = statement.where(col(Ticket.department_id) == department_id)
    return list(session.exec(statement).all())


def get_ticket_counts_by_status(
    session: Session,
    department_id: int | None,
) -> list[tuple[str, int]]:
    """Count tickets by lifecycle status within an optional department scope."""
    statement = (
        select(col(Ticket.status), func.count(col(Ticket.id)))
        .group_by(col(Ticket.status))
        .order_by(col(Ticket.status))
    )
    if department_id is not None:
        statement = statement.where(col(Ticket.department_id) == department_id)
    return list(session.exec(statement).all())


def get_ticket_counts_by_language(
    session: Session,
    department_id: int | None,
) -> list[tuple[str, int]]:
    """Count tickets by language within an optional department scope."""
    statement = (
        select(col(Ticket.language), func.count(col(Ticket.id)))
        .group_by(col(Ticket.language))
        .order_by(col(Ticket.language))
    )
    if department_id is not None:
        statement = statement.where(col(Ticket.department_id) == department_id)
    return list(session.exec(statement).all())


def get_total_ticket_count(session: Session, department_id: int | None) -> int:
    """Count all tickets within an optional department scope."""
    statement = select(func.count(col(Ticket.id)))
    if department_id is not None:
        statement = statement.where(col(Ticket.department_id) == department_id)
    return int(session.exec(statement).one())


def get_resolved_ticket_times(
    session: Session,
    department_id: int | None,
) -> list[tuple[datetime, datetime]]:
    """Return creation and resolution timestamps for scoped resolved tickets."""
    statement = select(col(Ticket.created_at), col(Ticket.resolved_at)).where(
        col(Ticket.resolved_at).is_not(None)
    )
    if department_id is not None:
        statement = statement.where(col(Ticket.department_id) == department_id)
    return [
        (created_at, resolved_at)
        for created_at, resolved_at in session.exec(statement).all()
        if resolved_at is not None
    ]
