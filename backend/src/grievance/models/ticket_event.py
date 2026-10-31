"""Ticket status event table."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class TicketEvent(SQLModel, table=True):
    """An auditable status change or note associated with a ticket."""

    __tablename__ = "ticket_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticket_id: UUID = Field(foreign_key="tickets.id", index=True)
    from_status: str | None = Field(default=None, max_length=32)
    to_status: str = Field(max_length=32)
    actor_type: str = Field(max_length=16)
    officer_id: int | None = Field(default=None, foreign_key="officers.id", index=True)
    note: str | None = Field(default=None)
    is_public: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
