"""Ticket creation and validated status-transition business logic."""

import secrets
import string
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from grievance.core.config import Settings
from grievance.core.exceptions import DomainError
from grievance.models import Department, Ticket, TicketEvent
from grievance.nlp.template_loader import load_templates
from grievance.repositories.department_repository import get_department_by_id
from grievance.repositories.ticket_repository import (
    add_ticket_event,
    create_ticket,
    get_ticket_by_public_id,
    list_public_ticket_events,
    update_ticket,
)
from grievance.schemas.chat import PublicTicketEventResponse, PublicTicketResponse

TicketActor = Literal["system", "officer", "citizen"]
ID_ALPHABET = string.ascii_uppercase + string.digits
PUBLIC_ID_RANDOM_LENGTH = 4
MAX_PUBLIC_ID_ATTEMPTS = 5
VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "FILED": frozenset({"ASSIGNED", "ESCALATED"}),
    "ASSIGNED": frozenset({"IN_PROGRESS", "ESCALATED"}),
    "IN_PROGRESS": frozenset({"RESOLVED", "ESCALATED"}),
    "RESOLVED": frozenset(),
    "ESCALATED": frozenset({"IN_PROGRESS", "RESOLVED"}),
}
STATUS_TEMPLATE_KEYS = {
    "FILED": "filed",
    "ASSIGNED": "assigned",
    "IN_PROGRESS": "in_progress",
    "RESOLVED": "resolved",
    "ESCALATED": "escalated",
}


def department_display_name(department: Department, language_code: str) -> str:
    """Return a department name in the ticket's supported reply language."""
    if language_code == "hi":
        return department.name_hi
    if language_code == "gu":
        return department.name_gu
    return department.name_en


def ticket_status_label(status: str, language_code: str) -> str:
    """Return a ticket status using the registered language's fixed template."""
    status_key = STATUS_TEMPLATE_KEYS.get(status)
    if status_key is None:
        raise ValueError(f"Unsupported ticket status: {status}")
    templates = load_templates(language_code)
    return str(getattr(templates.status_labels, status_key))


def generate_public_id(prefix: str, now: datetime | None = None) -> str:
    """Generate an FMC-style public ID using the supplied prefix and current UTC date."""
    current_time = now or datetime.now(UTC)
    random_part = "".join(secrets.choice(ID_ALPHABET) for _ in range(PUBLIC_ID_RANDOM_LENGTH))
    return f"{prefix}-{current_time.strftime('%y%m%d')}-{random_part}"


class TicketService:
    """Create tickets and enforce the ticket lifecycle without owning transactions."""

    def __init__(
        self,
        session: Session,
        settings: Settings,
        public_id_generator: Callable[[str], str] = generate_public_id,
    ) -> None:
        """Bind ticket operations to the caller's session and configured ID prefix."""
        self._session = session
        self._settings = settings
        self._public_id_generator = public_id_generator

    def create_ticket(
        self,
        conversation_id: UUID,
        department_id: int,
        complaint_text: str,
        language: str,
        location_text: str,
        contact_phone: str | None = None,
        predicted_confidence: float | None = None,
    ) -> Ticket:
        """Create a filed ticket and its initial public event."""
        for _ in range(MAX_PUBLIC_ID_ATTEMPTS):
            public_id = self._public_id_generator(self._settings.ticket_id_prefix)
            if get_ticket_by_public_id(self._session, public_id) is not None:
                continue

            ticket = Ticket(
                public_id=public_id,
                conversation_id=conversation_id,
                department_id=department_id,
                complaint_text=complaint_text,
                language=language,
                location_text=location_text,
                contact_phone=contact_phone,
                predicted_confidence=predicted_confidence,
                status="FILED",
            )
            try:
                with self._session.begin_nested():
                    create_ticket(self._session, ticket)
            except IntegrityError:
                if get_ticket_by_public_id(self._session, public_id) is not None:
                    continue
                raise

            add_ticket_event(
                self._session,
                TicketEvent(
                    ticket_id=ticket.id,
                    from_status=None,
                    to_status="FILED",
                    actor_type="citizen",
                    is_public=True,
                ),
            )
            return ticket

        raise RuntimeError(
            f"Unable to generate a unique ticket ID after {MAX_PUBLIC_ID_ATTEMPTS} attempts"
        )

    def transition_status(
        self,
        public_id: str,
        new_status: str,
        actor_type: TicketActor,
        officer_id: int | None = None,
        note: str | None = None,
        is_public: bool = False,
    ) -> Ticket:
        """Apply an allowed status transition and append its audit event."""
        ticket = get_ticket_by_public_id(self._session, public_id)
        if ticket is None:
            raise DomainError(
                code="TICKET_NOT_FOUND",
                message="Ticket not found",
                status_code=404,
            )

        current_status = ticket.status
        allowed_targets = VALID_TRANSITIONS.get(current_status)
        if allowed_targets is None or new_status not in allowed_targets:
            raise DomainError(
                code="INVALID_TRANSITION",
                message="Ticket status transition is not allowed",
                status_code=409,
                details={"from_status": current_status, "to_status": new_status},
            )

        timestamp = datetime.now(UTC)
        ticket.status = new_status
        ticket.status_changed_at = timestamp
        if new_status == "RESOLVED":
            ticket.resolved_at = timestamp
        update_ticket(self._session, ticket)
        add_ticket_event(
            self._session,
            TicketEvent(
                ticket_id=ticket.id,
                from_status=current_status,
                to_status=new_status,
                actor_type=actor_type,
                officer_id=officer_id,
                note=note,
                is_public=is_public,
            ),
        )
        return ticket

    def get_public_status(self, public_id: str) -> PublicTicketResponse:
        """Return a ticket's public fields and explicitly public event history."""
        ticket = get_ticket_by_public_id(self._session, public_id)
        if ticket is None:
            raise DomainError(
                code="TICKET_NOT_FOUND",
                message="Ticket not found",
                status_code=404,
            )
        department = get_department_by_id(self._session, ticket.department_id)
        if department is None:
            raise DomainError(
                code="DEPARTMENT_NOT_FOUND",
                message="Department data is not available",
                status_code=503,
            )
        department_name = department_display_name(department, ticket.language)
        events = list_public_ticket_events(self._session, ticket.id)
        return PublicTicketResponse(
            public_id=ticket.public_id,
            status=ticket_status_label(ticket.status, ticket.language),
            department=department_name,
            location=ticket.location_text,
            created_at=ticket.created_at,
            updated_at=ticket.status_changed_at,
            public_events=[
                PublicTicketEventResponse(
                    from_status=(
                        ticket_status_label(event.from_status, ticket.language)
                        if event.from_status is not None
                        else None
                    ),
                    to_status=ticket_status_label(event.to_status, ticket.language),
                    note=event.note,
                    created_at=event.created_at,
                )
                for event in events
            ],
        )
