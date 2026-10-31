"""Database integration tests for department persistence."""

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from grievance.models import Department
from grievance.repositories.department_repository import get_department_by_code


def test_department_repository_reads_from_database() -> None:
    """Persist and retrieve a department using the repository query."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        department = Department(
            code="WATER",
            name_en="Water Supply",
            name_hi="जल आपूर्ति",
            name_gu="પાણી પુરવઠો",
            sla_hours=24,
        )
        session.add(department)
        session.commit()

        result = get_department_by_code(session, "WATER")

    assert result is not None
    assert result.name_en == "Water Supply"
