"""Public ticket status API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlmodel import Session

from grievance.core.database import get_session
from grievance.schemas.chat import PublicTicketResponse
from grievance.services.ticket_service import TicketService

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


@router.get("/{public_id}", response_model=PublicTicketResponse)
def get_ticket_status(
    public_id: Annotated[str, Path(min_length=1, max_length=32)],
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> PublicTicketResponse:
    """Return only the public status, location, department, and event history."""
    return TicketService(session, request.app.state.settings).get_public_status(public_id)
