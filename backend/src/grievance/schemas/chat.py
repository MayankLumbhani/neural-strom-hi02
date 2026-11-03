"""Typed chat service and API response schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TicketStatusCode = Literal["FILED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "ESCALATED"]


class ChatReply(BaseModel):
    """Fixed reply text and optional department choices."""

    text: str
    quick_replies: list[str] = Field(default_factory=list)


class ChatTicketSummary(BaseModel):
    """Public ticket summary included in chat responses."""

    ticket_id: str
    department: str
    status: str


class ChatResponse(BaseModel):
    """Conversation state, localized reply, and optional new or looked-up ticket."""

    conversation_id: UUID
    state: str
    language: str
    language_tier: int = Field(ge=1)
    reply: ChatReply
    ticket: ChatTicketSummary | None = None


class ChatMessageRequest(BaseModel):
    """Validated request body for a citizen chat message."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    conversation_id: UUID | None = None


class PublicTicketEventResponse(BaseModel):
    """Public status event without private notes or actor details."""

    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime


class PublicTicketResponse(BaseModel):
    """Public ticket status and explicitly public event history."""

    public_id: str
    language: str
    status_code: TicketStatusCode
    status: str
    department: str
    location: str
    created_at: datetime
    updated_at: datetime
    public_events: list[PublicTicketEventResponse] = Field(default_factory=list)
