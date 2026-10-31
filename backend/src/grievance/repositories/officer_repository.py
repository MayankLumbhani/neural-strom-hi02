"""Officer persistence operations."""

from sqlmodel import Session, select

from grievance.models import Officer


def get_officer_by_username(session: Session, username: str) -> Officer | None:
    """Find an officer by their unique username."""
    return session.exec(select(Officer).where(Officer.username == username)).one_or_none()


def upsert_officer(session: Session, officer: Officer) -> Officer:
    """Insert an officer or update its seeded fields by username."""
    existing = get_officer_by_username(session, officer.username)
    if existing is None:
        session.add(officer)
        session.flush()
        return officer

    existing.password_hash = officer.password_hash
    existing.role = officer.role
    existing.department_id = officer.department_id
    existing.is_active = officer.is_active
    session.flush()
    return existing
