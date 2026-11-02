"""Application background scheduler configuration."""

from datetime import UTC

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from grievance.core.config import Settings
from grievance.jobs.escalation import run_escalation_job

ESCALATION_JOB_ID = "ticket-sla-escalation"


def create_scheduler(settings: Settings) -> BackgroundScheduler:
    """Create a scheduler with one coalesced, non-overlapping escalation job."""
    scheduler = BackgroundScheduler(timezone=UTC)
    scheduler.add_job(
        run_escalation_job,
        trigger=IntervalTrigger(
            seconds=settings.escalation_interval_seconds,
            timezone=UTC,
        ),
        args=[settings],
        id=ESCALATION_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
