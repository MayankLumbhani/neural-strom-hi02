"""Typed chat service and API response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


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
    reply: ChatReply
    ticket: ChatTicketSummary | None = None
