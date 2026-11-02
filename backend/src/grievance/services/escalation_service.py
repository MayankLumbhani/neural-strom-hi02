"""Business logic for escalating tickets that exceed department SLAs."""

from datetime import UTC, datetime

from sqlmodel import Session

from grievance.core.config import Settings
from grievance.repositories.escalation_repository import escalate_overdue_tickets


class EscalationService:
    """Apply configured SLA rules to active tickets."""

    def __init__(self, session: Session, settings: Settings) -> None:
        """Bind escalation operations to a request session and application settings."""
        self._session = session
        self._settings = settings

    def run(self, now: datetime | None = None) -> int:
        """Escalate all overdue tickets and return the number changed."""
        return escalate_overdue_tickets(
            self._session,
            now or datetime.now(UTC),
            self._settings.demo_mode,
        )
