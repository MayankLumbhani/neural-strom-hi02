"""Reusable authentication and authorization dependencies."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from grievance.core.database import get_session
from grievance.core.exceptions import DomainError
from grievance.models import Officer
from grievance.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_officer(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> Officer:
    """Authenticate a bearer token and reload its active officer account."""
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise DomainError(
            code="UNAUTHENTICATED",
            message="A valid bearer token is required",
            status_code=401,
        )
    return AuthService(session, request.app.state.settings).authenticate(credentials.credentials)


def require_roles(*allowed_roles: str) -> Callable[..., Officer]:
    """Create a dependency that requires one of the specified account roles."""

    def role_dependency(
        officer: Annotated[Officer, Depends(get_current_officer)],
    ) -> Officer:
        """Reject authenticated accounts whose role is not permitted."""
        if officer.role not in allowed_roles:
            raise DomainError(
                code="FORBIDDEN",
                message="This account is not authorized for this operation",
                status_code=403,
            )
        return officer

    return role_dependency
