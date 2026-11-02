"""Officer credential verification and access-token authentication."""

from sqlmodel import Session

from grievance.core.config import Settings
from grievance.core.exceptions import DomainError
from grievance.core.security import create_access_token, decode_access_token, verify_password
from grievance.models import Officer
from grievance.repositories.department_repository import get_department_by_id
from grievance.repositories.officer_repository import get_officer_by_username
from grievance.schemas.auth import LoginResponse

ALLOWED_ROLES = frozenset({"ADMIN", "DEPARTMENT_OFFICER"})


class AuthService:
    """Authenticate active officers and issue signed access tokens."""

    def __init__(self, session: Session, settings: Settings) -> None:
        """Bind credential operations to the request session and settings."""
        self._session = session
        self._settings = settings

    def login(self, username: str, password: str) -> LoginResponse:
        """Verify credentials and return an access token without exposing secrets."""
        officer = get_officer_by_username(self._session, username)
        if (
            officer is None
            or not officer.is_active
            or not verify_password(password, officer.password_hash)
            or officer.role not in ALLOWED_ROLES
        ):
            raise DomainError(
                code="INVALID_CREDENTIALS",
                message="Username or password is incorrect",
                status_code=401,
            )

        secret = self._jwt_secret()
        department_code: str | None = None
        if officer.department_id is not None:
            department = get_department_by_id(self._session, officer.department_id)
            if department is None:
                raise DomainError(
                    code="OFFICER_DEPARTMENT_UNAVAILABLE",
                    message="Officer department data is not available",
                    status_code=503,
                )
            department_code = department.code

        return LoginResponse(
            access_token=create_access_token(
                officer.username,
                secret,
                self._settings.jwt_expire_minutes,
            ),
            role=officer.role,
            department=department_code,
        )

    def authenticate(self, token: str) -> Officer:
        """Verify a bearer token and reload its active account from the database."""
        try:
            username = decode_access_token(token, self._jwt_secret())
        except ValueError as error:
            raise DomainError(
                code="INVALID_TOKEN",
                message="Access token is invalid or expired",
                status_code=401,
            ) from error

        officer = get_officer_by_username(self._session, username)
        if officer is None or not officer.is_active:
            raise DomainError(
                code="INVALID_TOKEN",
                message="Access token is invalid or expired",
                status_code=401,
            )
        return officer

    def _jwt_secret(self) -> str:
        """Return the configured JWT signing key or report a configuration error."""
        if self._settings.jwt_secret is None:
            raise DomainError(
                code="AUTH_NOT_CONFIGURED",
                message="JWT_SECRET must be configured before authentication is available",
                status_code=503,
            )
        secret = self._settings.jwt_secret.get_secret_value()
        if not secret:
            raise DomainError(
                code="AUTH_NOT_CONFIGURED",
                message="JWT_SECRET must be configured before authentication is available",
                status_code=503,
            )
        return secret
