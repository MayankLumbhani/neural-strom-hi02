"""Department persistence operations."""

from sqlmodel import Session, select

from grievance.models import Department


def get_department_by_code(session: Session, code: str) -> Department | None:
    """Find a department by its unique code."""
    return session.exec(select(Department).where(Department.code == code)).one_or_none()
