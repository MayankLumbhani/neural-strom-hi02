"""Department-scoped ticket management for authenticated staff."""

from sqlmodel import Session

from grievance.core.config import Settings
from grievance.core.exceptions import DomainError
from grievance.models import Department, Officer, Ticket, TicketEvent
from grievance.repositories.ticket_repository import (
    get_scoped_ticket,
    list_ticket_events,
    list_tickets,
)
from grievance.schemas.admin import (
    AdminTicketEventResponse,
    AdminTicketListResponse,
    AdminTicketResponse,
    AdminTicketSummaryResponse,
)
from grievance.services.ticket_service import TicketService


class AdminTicketService:
    """Provide ticket operations scoped by the authenticated staff account."""

    def __init__(self, session: Session, settings: Settings) -> None:
        """Bind staff ticket operations to a request session and settings."""
        self._session = session
        self._settings = settings

    def list_tickets(
        self,
        officer: Officer,
        status: str | None,
        department_code: str | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> AdminTicketListResponse:
        """Return a paginated queue, enforcing officer department scope in the query."""
        department_id = self._department_scope(officer)
        rows, total = list_tickets(
            self._session,
            department_id,
            status,
            department_code,
            search,
            (page - 1) * page_size,
            page_size,
        )
        return AdminTicketListResponse(
            items=[self._summary(ticket, department) for ticket, department in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_ticket(self, officer: Officer, public_id: str) -> AdminTicketResponse:
        """Return a ticket and full event history only within the officer's scope."""
        department_id = self._department_scope(officer)
        scoped = get_scoped_ticket(self._session, public_id, department_id)
        if scoped is None:
            raise self._not_found()
        ticket, department = scoped
        return self._detail(ticket, department, list_ticket_events(self._session, ticket.id))

    def update_status(
        self,
        officer: Officer,
        public_id: str,
        new_status: str,
        note: str | None,
        is_public: bool,
    ) -> AdminTicketResponse:
        """Apply an authorized status transition and return its updated ticket detail."""
        department_id = self._department_scope(officer)
        scoped = get_scoped_ticket(self._session, public_id, department_id)
        if scoped is None:
            raise self._not_found()
        TicketService(self._session, self._settings).transition_status(
            public_id,
            new_status,
            actor_type="officer",
            officer_id=officer.id,
            note=note,
            is_public=is_public,
        )
        return self.get_ticket(officer, public_id)

    @staticmethod
    def _department_scope(officer: Officer) -> int | None:
        """Return unrestricted admin scope or require an officer department."""
        if officer.role == "ADMIN":
            return None
        if officer.role == "DEPARTMENT_OFFICER" and officer.department_id is not None:
            return officer.department_id
        raise DomainError(
            code="FORBIDDEN",
            message="This account is not authorized for ticket operations",
            status_code=403,
        )

    @staticmethod
    def _not_found() -> DomainError:
        """Create a scope-safe not-found response for absent or inaccessible tickets."""
        return DomainError(
            code="TICKET_NOT_FOUND",
            message="Ticket not found",
            status_code=404,
        )

    @staticmethod
    def _summary(ticket: Ticket, department: Department) -> AdminTicketSummaryResponse:
        """Map persisted ticket fields to a staff queue response."""
        return AdminTicketSummaryResponse(
            public_id=ticket.public_id,
            status=ticket.status,
            department=department.code,
            location=ticket.location_text,
            language=ticket.language,
            created_at=ticket.created_at,
            status_changed_at=ticket.status_changed_at,
            escalation_level=ticket.escalation_level,
        )

    @classmethod
    def _detail(
        cls,
        ticket: Ticket,
        department: Department,
        events: list[TicketEvent],
    ) -> AdminTicketResponse:
        """Map a ticket and event history to the authenticated detail response."""
        return AdminTicketResponse(
            **cls._summary(ticket, department).model_dump(),
            complaint_text=ticket.complaint_text,
            contact_phone=ticket.contact_phone,
            resolved_at=ticket.resolved_at,
            events=[
                AdminTicketEventResponse(
                    id=event.id,
                    from_status=event.from_status,
                    to_status=event.to_status,
                    actor_type=event.actor_type,
                    note=event.note,
                    is_public=event.is_public,
                    created_at=event.created_at,
                )
                for event in events
            ],
        )
