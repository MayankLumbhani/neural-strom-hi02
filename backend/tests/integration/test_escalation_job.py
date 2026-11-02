"""Integration tests for SLA escalation and scheduler configuration."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from grievance.app import create_app
from grievance.core.config import Settings
from grievance.jobs.scheduler import ESCALATION_JOB_ID, create_scheduler
from grievance.models import Conversation, Department, Ticket, TicketEvent
from grievance.nlp.classifier import FakeClassifier
from grievance.repositories.ticket_repository import create_ticket
from grievance.services.escalation_service import EscalationService


def _create_old_ticket(session: Session, now: datetime) -> UUID:
    """Create one ticket whose status has been unchanged for 25 minutes."""
    department = session.exec(select(Department).where(Department.code == "WATER")).one()
    conversation = Conversation(language="en")
    session.add(conversation)
    session.flush()
    ticket = Ticket(
        public_id="FMC-261102-OLD1",
        conversation_id=conversation.id,
        department_id=department.id,
        complaint_text="Synthetic overdue water complaint",
        language="en",
        location_text="Ward 4",
        status="FILED",
        status_changed_at=now - timedelta(minutes=25),
    )
    create_ticket(session, ticket)
    session.add(
        TicketEvent(
            ticket_id=ticket.id,
            from_status=None,
            to_status="FILED",
            actor_type="citizen",
            is_public=True,
        )
    )
    session.commit()
    return ticket.id


def test_demo_mode_escalates_overdue_ticket_once_and_records_event() -> None:
    """Use SLA minutes in demo mode and make repeated runs idempotent."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    now = datetime.now(UTC)
    with Session(engine) as session:
        session.add(
            Department(
                code="WATER",
                name_en="Water Supply",
                name_hi="जल आपूर्ति",
                name_gu="પાણી પુરવઠો",
                sla_hours=24,
            )
        )
        session.commit()
        ticket_id = _create_old_ticket(session, now)
        service = EscalationService(
            session,
            Settings(_env_file=None, demo_mode=True),
        )

        assert service.run(now) == 1
        session.commit()
        assert service.run(now + timedelta(minutes=10)) == 0
        session.commit()

        ticket = session.get(Ticket, ticket_id)
        events = session.exec(select(TicketEvent).where(TicketEvent.ticket_id == ticket_id)).all()

    engine.dispose()
    assert ticket is not None
    assert ticket.status == "ESCALATED"
    assert ticket.escalation_level == 1
    escalation_events = [event for event in events if event.to_status == "ESCALATED"]
    assert len(escalation_events) == 1
    assert escalation_events[0].from_status == "FILED"
    assert escalation_events[0].actor_type == "system"


def test_production_mode_uses_sla_hours() -> None:
    """Do not escalate a ticket that exceeds demo minutes but not the SLA hours."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    now = datetime.now(UTC)
    with Session(engine) as session:
        session.add(
            Department(
                code="WATER",
                name_en="Water Supply",
                name_hi="जल आपूर्ति",
                name_gu="પાણી પુરવઠો",
                sla_hours=24,
            )
        )
        session.commit()
        ticket_id = _create_old_ticket(session, now)

        changed = EscalationService(
            session,
            Settings(_env_file=None, demo_mode=False),
        ).run(now)
        ticket = session.get(Ticket, ticket_id)

    engine.dispose()
    assert changed == 0
    assert ticket is not None
    assert ticket.status == "FILED"
    assert ticket.escalation_level == 0


def test_scheduler_registers_single_non_overlapping_escalation_job() -> None:
    """Schedule one coalesced job using the configured interval."""
    settings = Settings(_env_file=None, escalation_interval_seconds=37)
    scheduler: BackgroundScheduler = create_scheduler(settings)
    scheduler.start(paused=True)
    try:
        job = scheduler.get_job(ESCALATION_JOB_ID)

        assert job is not None
        assert job.trigger.interval.total_seconds() == 37
        assert job.max_instances == 1
        assert job.coalesce is True
    finally:
        scheduler.shutdown(wait=False)


def test_app_starts_and_stops_scheduler_when_database_is_configured() -> None:
    """Tie scheduler lifetime to the API lifespan when persistence is configured."""
    settings = Settings(
        _env_file=None,
        database_url="sqlite://",
        escalation_interval_seconds=3600,
    )
    app = create_app(settings, classifier=FakeClassifier())

    with TestClient(app):
        scheduler: BackgroundScheduler = app.state.scheduler
        assert scheduler.running

    assert not scheduler.running
