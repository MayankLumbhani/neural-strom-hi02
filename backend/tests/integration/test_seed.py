"""Integration tests for initial synthetic database data."""

import bcrypt
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from grievance.core.config import Settings
from grievance.core.security import hash_password
from grievance.models import Department, Officer
from grievance.seed import DEPARTMENTS, seed_database


def _seed_settings() -> Settings:
    """Build test-only demo credentials without loading local environment files."""
    return Settings(
        _env_file=None,
        demo_officer_username="demo-officer",
        demo_officer_password="synthetic-officer-password",
        demo_admin_username="demo-admin",
        demo_admin_password="synthetic-admin-password",
    )


def test_seed_database_is_idempotent_and_hashes_demo_passwords() -> None:
    """Seed multilingual departments and accounts without duplicate rows or hash churn."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        seed_database(session, _seed_settings())
        session.commit()
        first_hashes = {
            officer.username: officer.password_hash
            for officer in session.exec(select(Officer)).all()
        }

        seed_database(session, _seed_settings())
        session.commit()

        departments = session.exec(select(Department)).all()
        officers = session.exec(select(Officer)).all()

    assert len(departments) == 9
    assert {department.code for department in departments} == {
        department.code for department in DEPARTMENTS
    }
    assert {
        department.code: (
            department.name_en,
            department.name_hi,
            department.name_gu,
            department.sla_hours,
        )
        for department in departments
    } == {
        seed.code: (seed.name_en, seed.name_hi, seed.name_gu, seed.sla_hours)
        for seed in DEPARTMENTS
    }
    assert len(officers) == 2
    assert {officer.username: officer.password_hash for officer in officers} == first_hashes
    assert {officer.username: officer.role for officer in officers} == {
        "demo-officer": "DEPARTMENT_OFFICER",
        "demo-admin": "ADMIN",
    }
    water_department = next(department for department in departments if department.code == "WATER")
    officer_account = next(officer for officer in officers if officer.username == "demo-officer")
    admin_account = next(officer for officer in officers if officer.username == "demo-admin")
    assert officer_account.department_id == water_department.id
    assert admin_account.department_id is None
    assert all(officer.password_hash != "synthetic-officer-password" for officer in officers)
    assert bcrypt.checkpw(
        b"synthetic-officer-password",
        first_hashes["demo-officer"].encode("ascii"),
    )
    assert bcrypt.checkpw(
        b"synthetic-admin-password",
        first_hashes["demo-admin"].encode("ascii"),
    )


@pytest.mark.parametrize(
    "password",
    ["short", "x" * 73],
)
def test_hash_password_rejects_unsupported_password_lengths(password: str) -> None:
    """Reject passwords outside bcrypt's supported safe byte range."""
    with pytest.raises(ValueError, match="12 and 72 UTF-8 bytes"):
        hash_password(password)
