"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from grievance.core.database import get_session
from grievance.schemas.auth import LoginRequest, LoginResponse
from grievance.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> LoginResponse:
    """Verify officer credentials and return a signed bearer token."""
    settings = request.app.state.settings
    return AuthService(session, settings).login(payload.username, payload.password)
