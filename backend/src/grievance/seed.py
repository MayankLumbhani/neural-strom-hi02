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
    """Synthetic multilingual department data, aliases, and its starting SLA."""

    code: str
    name_en: str
    name_hi: str
    name_gu: str
    sla_hours: int
    aliases: tuple[str, ...] = ()

    def localized_name(self, language_code: str) -> str:
        """Return the seed name for a supported language, falling back to English."""
        if language_code == "hi":
            return self.name_hi
        if language_code == "gu":
            return self.name_gu
        return self.name_en


DEPARTMENTS = (
    DepartmentSeed(
        "WATER",
        "Water Supply",
        "जल आपूर्ति",
        "પાણી પુરવઠો",
        24,
        (
            "water",
            "water supply",
            "paani",
            "pani",
            "jal",
            "tap",
            "nal",
            "नल",
            "पानी",
            "जल",
            "નળ",
            "પાણી",
            "જળ",
        ),
    ),
    DepartmentSeed(
        "ROADS",
        "Roads and Infrastructure",
        "सड़क एवं आधारभूत संरचना",
        "રસ્તા અને ઇન્ફ્રાસ્ટ્રક્ચર",
        48,
        (
            "road",
            "roads",
            "rasta",
            "sadak",
            "pothole",
            "potholes",
            "सड़क",
            "रास्ता",
            "गड्ढा",
            "સડક",
            "રસ્તો",
            "ગડ્ડો",
        ),
    ),
    DepartmentSeed(
        "SANITATION",
        "Sanitation and Waste",
        "स्वच्छता एवं कचरा",
        "સફાઈ અને કચરો",
        24,
        (
            "sanitation",
            "waste",
            "garbage",
            "kachra",
            "safai",
            "कचरा",
            "सफाई",
            "स्वच्छता",
            "કચરો",
            "સફાઈ",
        ),
    ),
    DepartmentSeed(
        "ELECTRICITY",
        "Electricity",
        "बिजली",
        "વીજળી",
        12,
        (
            "electricity",
            "electric",
            "power",
            "power cut",
            "bijli",
            "current",
            "बिजली",
            "करंट",
            "વીજળી",
            "વીજ",
        ),
    ),
    DepartmentSeed(
        "STREETLIGHT",
        "Street Lights",
        "स्ट्रीट लाइट",
        "સ્ટ્રીટ લાઇટ",
        24,
        (
            "street light",
            "street lights",
            "streetlight",
            "streetlights",
            "lamp",
            "lamp post",
            "स्ट्रीट लाइट",
            "સ્ટ્રીટ લાઇટ",
        ),
    ),
    DepartmentSeed(
        "DRAINAGE",
        "Drainage and Sewage",
        "जल निकासी एवं सीवेज",
        "ગટર અને ગંદા પાણી",
        12,
        (
            "drainage",
            "drain",
            "sewage",
            "sewer",
            "nali",
            "gutter",
            "जल निकासी",
            "सीवेज",
            "नाली",
            "ગટર",
            "ગંદા પાણી",
            "ડ્રેનેજ",
        ),
    ),
    DepartmentSeed(
        "HEALTH",
        "Public Health",
        "जन स्वास्थ्य",
        "જાહેર આરોગ્ય",
        24,
        (
            "health",
            "public health",
            "hospital",
            "clinic",
            "doctor",
            "disease",
            "स्वास्थ्य",
            "अस्पताल",
            "बीमारी",
            "આરોગ્ય",
            "હોસ્પિટલ",
            "બીમારી",
        ),
    ),
    DepartmentSeed(
        "TAX",
        "Property Tax and Billing",
        "संपत्ति कर एवं बिलिंग",
        "મિલકત વેરો અને બિલિંગ",
        72,
        (
            "tax",
            "property tax",
            "billing",
            "bill",
            "कर",
            "संपत्ति कर",
            "बिल",
            "વેરો",
            "મિલકત વેરો",
            "બિલ",
        ),
    ),
    DepartmentSeed(
        "OTHER",
        "General or Unclear",
        "सामान्य या अस्पष्ट",
        "સામાન્ય અથવા અસ્પષ્ટ",
        48,
        ("other", "general", "unclear", "anything", "अन्य", "सामान्य", "અન્ય", "સામાન્ય"),
    ),
)


def _required_value(value: str | None, setting_name: str) -> str:
    """Return a required non-empty seed setting or raise a clear error."""
    if value is None or not value.strip():
        raise ValueError(f"{setting_name} must be configured before seeding demo accounts")
    return value


def _required_password(secret: SecretStr | None, setting_name: str) -> str:
    """Return a required seed password without exposing it in error messages."""
    if secret is None or not secret.get_secret_value().strip():
        raise ValueError(f"{setting_name.upper()} must be configured before seeding demo accounts")
    return secret.get_secret_value()


def _seed_departments(session: Session) -> None:
    """Create or update every synthetic department."""
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


def _missing_demo_settings(settings: Settings) -> list[str]:
    """Return names of missing demo account settings without exposing their values."""
    missing: list[str] = []
    if settings.demo_officer_username is None or not settings.demo_officer_username.strip():
        missing.append("DEMO_OFFICER_USERNAME")
    if (
        settings.demo_officer_password is None
        or not settings.demo_officer_password.get_secret_value().strip()
    ):
        missing.append("DEMO_OFFICER_PASSWORD")
    if not settings.demo_officer_department_code.strip():
        missing.append("DEMO_OFFICER_DEPARTMENT_CODE")
    if settings.demo_admin_username is None or not settings.demo_admin_username.strip():
        missing.append("DEMO_ADMIN_USERNAME")
    if (
        settings.demo_admin_password is None
        or not settings.demo_admin_password.get_secret_value().strip()
    ):
        missing.append("DEMO_ADMIN_PASSWORD")
    return missing


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


def _seed_demo_accounts(session: Session, settings: Settings) -> int:
    """Create demo accounts when configuration is complete and valid."""
    officer_username = _required_value(
        settings.demo_officer_username,
        "DEMO_OFFICER_USERNAME",
    )
    admin_username = _required_value(settings.demo_admin_username, "DEMO_ADMIN_USERNAME")
    if officer_username == admin_username:
        logger.warning("seed.demo_accounts.skipped reason=duplicate_usernames")
        return 0

    officer_password = _required_password(
        settings.demo_officer_password,
        "demo_officer_password",
    )
    admin_password = _required_password(settings.demo_admin_password, "demo_admin_password")
    try:
        validate_password(officer_password)
        validate_password(admin_password)
    except ValueError:
        logger.warning("seed.demo_accounts.skipped reason=invalid_password")
        return 0

    officer_department_code = _required_value(
        settings.demo_officer_department_code,
        "DEMO_OFFICER_DEPARTMENT_CODE",
    )
    if get_department_by_code(session, officer_department_code) is None:
        logger.warning("seed.demo_accounts.skipped reason=unknown_department_code")
        return 0

    _seed_officer_account(
        session,
        officer_username,
        officer_password,
        officer_department_code,
    )
    _seed_admin_account(session, admin_username, admin_password)
    return 2


def seed_database(session: Session, settings: Settings) -> int:
    """Seed departments always and demo accounts only when enabled and configured."""
    _seed_departments(session)
    if not settings.demo_mode:
        logger.info("seed.demo_accounts.skipped reason=DEMO_MODE_disabled")
        return 0
    missing = _missing_demo_settings(settings)
    if missing:
        logger.warning(
            "seed.demo_accounts.skipped reason=incomplete_config settings=%s",
            ",".join(missing),
        )
        return 0
    return _seed_demo_accounts(session, settings)


def main() -> None:
    """Run the seed operation against the configured database."""
    settings = get_settings()
    configure_logging(settings.log_level)
    with Session(get_engine(settings)) as session, session.begin():
        accounts = seed_database(session, settings)
    logger.info("seed.completed departments=%d accounts=%d", len(DEPARTMENTS), accounts)


if __name__ == "__main__":
    main()
