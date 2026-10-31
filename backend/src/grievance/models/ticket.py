"""Grievance ticket table and query indexes."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class Ticket(SQLModel, table=True):
    """A grievance assigned to a municipal department."""

    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_department_status", "department_id", "status"),
        Index("ix_tickets_status_changed", "status", "status_changed_at"),
        UniqueConstraint("conversation_id", name="uq_tickets_conversation_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    public_id: str = Field(max_length=32, unique=True, index=True)
    conversation_id: UUID = Field(foreign_key="conversations.id")
    department_id: int = Field(foreign_key="departments.id")
    complaint_text: str
    language: str = Field(max_length=32)
    location_text: str
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str = Field(default="FILED", max_length=32)
    status_changed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    escalation_level: int = Field(default=0, ge=0)
    predicted_confidence: float | None = Field(default=None, ge=0, le=1)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    resolved_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
