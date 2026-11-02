"""Public chat API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from grievance.core.database import get_session
from grievance.core.exceptions import DomainError
from grievance.schemas.chat import ChatMessageRequest, ChatResponse
from grievance.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/messages", response_model=ChatResponse)
def post_chat_message(
    payload: ChatMessageRequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> ChatResponse:
    """Submit one citizen message to the persisted conversation service."""
    classifier = request.app.state.classifier
    if classifier is None:
        raise DomainError(
            code="CLASSIFIER_UNAVAILABLE",
            message="The complaint classifier is unavailable",
            status_code=503,
        )
    return ChatService(session, request.app.state.settings, classifier).handle_message(
        payload.text,
        payload.conversation_id,
    )
