"""Authenticated staff ticket endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlmodel import Session

from grievance.api.dependencies import require_roles
from grievance.core.database import get_session
from grievance.core.exceptions import DomainError
from grievance.models import Officer
from grievance.schemas.admin import (
    AdminTicketListResponse,
    AdminTicketResponse,
    AnalyticsSummaryResponse,
    TicketStatus,
    TicketStatusUpdateRequest,
)
from grievance.services.admin_ticket_service import AdminTicketService
from grievance.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
get_staff_officer = require_roles("ADMIN", "DEPARTMENT_OFFICER")


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    officer: Annotated[Officer, Depends(get_staff_officer)],
    session: Annotated[Session, Depends(get_session)],
) -> AnalyticsSummaryResponse:
    """Return ticket metrics scoped to the authenticated staff member."""
    return AnalyticsService(session).summary(officer)


@router.get("/tickets", response_model=AdminTicketListResponse)
def list_admin_tickets(
    request: Request,
    officer: Annotated[Officer, Depends(get_staff_officer)],
    session: Annotated[Session, Depends(get_session)],
    status: TicketStatus | None = None,
    department: Annotated[str | None, Query(max_length=50)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AdminTicketListResponse:
    """Return a filtered and paginated ticket queue within the staff scope."""
    if date_from is not None and date_to is not None and date_from > date_to:
        raise DomainError(
            code="INVALID_DATE_RANGE",
            message="The start date must not be after the end date",
            status_code=422,
        )
    service = AdminTicketService(session, request.app.state.settings)
    return service.list_tickets(
        officer,
        status,
        department,
        q,
        date_from,
        date_to,
        page,
        page_size,
    )


@router.get("/tickets/{public_id}", response_model=AdminTicketResponse)
def get_admin_ticket(
    public_id: Annotated[str, Path(min_length=1, max_length=32)],
    request: Request,
    officer: Annotated[Officer, Depends(get_staff_officer)],
    session: Annotated[Session, Depends(get_session)],
) -> AdminTicketResponse:
    """Return full ticket details and event history within the staff scope."""
    service = AdminTicketService(session, request.app.state.settings)
    return service.get_ticket(officer, public_id)


@router.patch("/tickets/{public_id}/status", response_model=AdminTicketResponse)
def update_admin_ticket_status(
    public_id: Annotated[str, Path(min_length=1, max_length=32)],
    payload: TicketStatusUpdateRequest,
    request: Request,
    officer: Annotated[Officer, Depends(get_staff_officer)],
    session: Annotated[Session, Depends(get_session)],
) -> AdminTicketResponse:
    """Apply a valid status transition and append an auditable event."""
    service = AdminTicketService(session, request.app.state.settings)
    return service.update_status(
        officer,
        public_id,
        payload.status,
        payload.note,
        payload.is_public,
    )
