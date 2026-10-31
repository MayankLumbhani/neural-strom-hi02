"""Conversation message table."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index, func
from sqlmodel import Field, SQLModel


class Message(SQLModel, table=True):
    """A citizen or bot message belonging to a conversation."""

    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversations.id")
    sender: str = Field(max_length=16)
    text: str
    language: str = Field(max_length=32)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
