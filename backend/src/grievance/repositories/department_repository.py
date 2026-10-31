"""Department persistence operations."""

from sqlmodel import Session, select

from grievance.models import Department


def get_department_by_code(session: Session, code: str) -> Department | None:
    """Find a department by its unique code."""
    return session.exec(select(Department).where(Department.code == code)).one_or_none()


def upsert_department(session: Session, department: Department) -> Department:
    """Insert a department or update its seeded fields by code."""
    existing = get_department_by_code(session, department.code)
    if existing is None:
        session.add(department)
        session.flush()
        return department

    existing.name_en = department.name_en
    existing.name_hi = department.name_hi
    existing.name_gu = department.name_gu
    existing.sla_hours = department.sla_hours
    session.flush()
    return existing
