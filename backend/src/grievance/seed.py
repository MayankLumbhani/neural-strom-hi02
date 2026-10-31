"""Seed the synthetic departments and demo accounts."""

from dataclasses import dataclass

from pydantic import SecretStr
from sqlmodel import Session

from grievance.core.config import Settings, get_settings
from grievance.core.database import get_engine
from grievance.core.logging import configure_logging, logger
from grievance.core.security import hash_password, validate_password, verify_password
from grievance.models import Department, Officer
from grievance.repositories.department_repository import (
    get_department_by_code,
    upsert_department,
)
from grievance.repositories.officer_repository import (
    get_officer_by_username,
    upsert_officer,
)


@dataclass(frozen=True)
class DepartmentSeed:
    """Synthetic multilingual department data and its starting SLA."""

    code: str
    name_en: str
    name_hi: str
    name_gu: str
    sla_hours: int


DEPARTMENTS = (
    DepartmentSeed("WATER", "Water Supply", "जल आपूर्ति", "પાણી પુરવઠો", 24),
    DepartmentSeed(
        "ROADS",
        "Roads and Infrastructure",
        "सड़क एवं आधारभूत संरचना",
        "રસ્તા અને ઇન્ફ્રાસ્ટ્રક્ચર",
        48,
    ),
    DepartmentSeed(
        "SANITATION",
        "Sanitation and Waste",
        "स्वच्छता एवं कचरा",
        "સફાઈ અને કચરો",
        24,
    ),
    DepartmentSeed("ELECTRICITY", "Electricity", "बिजली", "વીજળી", 12),
    DepartmentSeed("STREETLIGHT", "Street Lights", "स्ट्रीट लाइट", "સ્ટ્રીટ લાઇટ", 24),
    DepartmentSeed(
        "DRAINAGE",
        "Drainage and Sewage",
        "जल निकासी एवं सीवेज",
        "ગટર અને ગંદા પાણી",
        12,
    ),
    DepartmentSeed("HEALTH", "Public Health", "जन स्वास्थ्य", "જાહેર આરોગ્ય", 24),
    DepartmentSeed(
        "TAX",
        "Property Tax and Billing",
        "संपत्ति कर एवं बिलिंग",
        "મિલકત વેરો અને બિલિંગ",
        72,
    ),
    DepartmentSeed("OTHER", "General or Unclear", "सामान्य या अस्पष्ट", "સામાન્ય અથવા અસ્પષ્ટ", 48),
)


def _required_value(value: str | None, setting_name: str) -> str:
    """Return a required non-empty seed setting or raise a clear error."""
    if value is None or not value.strip():
        raise ValueError(f"{setting_name} must be configured before running make seed")
    return value


def _required_password(secret: SecretStr | None, setting_name: str) -> str:
    """Return a required seed password without exposing it in error messages."""
    if secret is None or not secret.get_secret_value().strip():
        raise ValueError(f"{setting_name.upper()} must be configured before running make seed")
    return secret.get_secret_value()


def _seed_officer_account(
    session: Session,
    username: str,
    password: str,
    department_code: str,
) -> None:
    """Create or update the synthetic department officer account."""
    department = get_department_by_code(session, department_code)
    if department is None or department.id is None:
        raise ValueError("DEMO_OFFICER_DEPARTMENT_CODE must match a seeded department code")

    existing = get_officer_by_username(session, username)
    password_hash = (
        existing.password_hash
        if existing is not None and verify_password(password, existing.password_hash)
        else hash_password(password)
    )
    upsert_officer(
        session,
        Officer(
            username=username,
            password_hash=password_hash,
            role="DEPARTMENT_OFFICER",
            department_id=department.id,
            is_active=True,
        ),
    )


def _seed_admin_account(session: Session, username: str, password: str) -> None:
    """Create or update the synthetic administrator account."""
    existing = get_officer_by_username(session, username)
    password_hash = (
        existing.password_hash
        if existing is not None and verify_password(password, existing.password_hash)
        else hash_password(password)
    )
    upsert_officer(
        session,
        Officer(
            username=username,
            password_hash=password_hash,
            role="ADMIN",
            department_id=None,
            is_active=True,
        ),
    )


def seed_database(session: Session, settings: Settings) -> None:
    """Seed departments and demo accounts using repository operations."""
    officer_username = _required_value(
        settings.demo_officer_username,
        "DEMO_OFFICER_USERNAME",
    )
    admin_username = _required_value(settings.demo_admin_username, "DEMO_ADMIN_USERNAME")
    if officer_username == admin_username:
        raise ValueError("DEMO_OFFICER_USERNAME and DEMO_ADMIN_USERNAME must be different")

    officer_password = _required_password(
        settings.demo_officer_password,
        "demo_officer_password",
    )
    admin_password = _required_password(settings.demo_admin_password, "demo_admin_password")
    validate_password(officer_password)
    validate_password(admin_password)
    officer_department_code = _required_value(
        settings.demo_officer_department_code,
        "DEMO_OFFICER_DEPARTMENT_CODE",
    )

    for seed in DEPARTMENTS:
        upsert_department(
            session,
            Department(
                code=seed.code,
                name_en=seed.name_en,
                name_hi=seed.name_hi,
                name_gu=seed.name_gu,
                sla_hours=seed.sla_hours,
            ),
        )

    _seed_officer_account(
        session,
        officer_username,
        officer_password,
        officer_department_code,
    )
    _seed_admin_account(session, admin_username, admin_password)


def main() -> None:
    """Run the seed operation against the configured database."""
    settings = get_settings()
    configure_logging(settings.log_level)
    with Session(get_engine(settings)) as session, session.begin():
        seed_database(session, settings)
    logger.info("seed.completed departments=%d accounts=2", len(DEPARTMENTS))


if __name__ == "__main__":
    main()
