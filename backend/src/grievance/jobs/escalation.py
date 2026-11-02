"""APScheduler callback for committing SLA escalations."""

from sqlmodel import Session

from grievance.core.config import Settings
from grievance.core.database import get_engine
from grievance.core.logging import logger
from grievance.services.escalation_service import EscalationService


def run_escalation_job(settings: Settings) -> int:
    """Run and commit one escalation batch against the configured database."""
    with Session(get_engine(settings)) as session:
        count = EscalationService(session, settings).run()
        session.commit()
    logger.info("escalation.completed", extra={"tickets_escalated": count})
    return count
