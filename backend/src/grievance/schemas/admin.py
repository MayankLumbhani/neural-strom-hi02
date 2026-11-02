"""Authenticated ticket-management request and response schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TicketStatus = Literal["FILED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "ESCALATED"]


class AdminTicketEventResponse(BaseModel):
    """Full event history entry visible to an authenticated staff member."""

    id: UUID
    from_status: str | None
    to_status: str
    actor_type: str
    note: str | None
    is_public: bool
    created_at: datetime


class AdminTicketSummaryResponse(BaseModel):
    """Ticket fields suitable for a filtered staff queue."""

    public_id: str
    status: str
    department: str
    location: str
    language: str
    created_at: datetime
    status_changed_at: datetime
    escalation_level: int


class AdminTicketResponse(AdminTicketSummaryResponse):
    """Ticket detail available to authenticated staff in scope."""

    complaint_text: str
    contact_phone: str | None
    resolved_at: datetime | None
    events: list[AdminTicketEventResponse] = Field(default_factory=list)


class AdminTicketListResponse(BaseModel):
    """Paginated staff ticket queue."""

    items: list[AdminTicketSummaryResponse]
    total: int
    page: int
    page_size: int


class TicketStatusUpdateRequest(BaseModel):
    """Validated status transition and optional auditable note."""

    model_config = ConfigDict(extra="forbid")

    status: TicketStatus
    note: str | None = Field(default=None, max_length=2000)
    is_public: bool = False
