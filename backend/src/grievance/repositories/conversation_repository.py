"""Conversation and message persistence operations."""

from uuid import UUID

from sqlmodel import Session, select

from grievance.models import Conversation, Message


def get_conversation(session: Session, conversation_id: UUID) -> Conversation | None:
    """Find a conversation by its public UUID."""
    return session.get(Conversation, conversation_id)


def create_conversation(session: Session, language: str) -> Conversation:
    """Create and flush a new conversation."""
    conversation = Conversation(language=language)
    session.add(conversation)
    session.flush()
    return conversation


def update_conversation(session: Session, conversation: Conversation) -> Conversation:
    """Flush updates to a conversation in the current transaction."""
    session.add(conversation)
    session.flush()
    return conversation


def add_message(
    session: Session,
    conversation_id: UUID,
    sender: str,
    text: str,
    language: str,
) -> Message:
    """Persist and flush a citizen or bot message."""
    message = Message(
        conversation_id=conversation_id,
        sender=sender,
        text=text,
        language=language,
    )
    session.add(message)
    session.flush()
    return message


def list_messages(session: Session, conversation_id: UUID) -> list[Message]:
    """Return messages for a conversation in creation order."""
    messages = session.exec(select(Message).where(Message.conversation_id == conversation_id)).all()
    return sorted(
        messages,
        key=lambda message: (message.created_at, str(message.id)),
    )
