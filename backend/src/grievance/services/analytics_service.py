"""Role-scoped ticket analytics aggregation."""

from datetime import UTC, datetime

from sqlmodel import Session

from grievance.core.exceptions import DomainError
from grievance.models import Officer
from grievance.repositories.analytics_repository import (
    get_resolved_ticket_times,
    get_ticket_counts_by_department,
    get_ticket_counts_by_language,
    get_ticket_counts_by_status,
    get_total_ticket_count,
)
from grievance.schemas.admin import (
    AnalyticsSummaryResponse,
    DepartmentTicketCount,
    TicketDimensionCount,
)


class AnalyticsService:
    """Aggregate ticket metrics for administrators or one officer department."""

    def __init__(self, session: Session) -> None:
        """Bind analytics queries to the request-scoped database session."""
        self._session = session

    def summary(self, officer: Officer) -> AnalyticsSummaryResponse:
        """Return counts and resolution duration within the caller's role scope."""
        department_id = self._department_scope(officer)
        resolved_times = get_resolved_ticket_times(self._session, department_id)
        durations_hours = [
            (self._as_utc(resolved_at) - self._as_utc(created_at)).total_seconds() / 3600
            for created_at, resolved_at in resolved_times
        ]
        return AnalyticsSummaryResponse(
            total_tickets=get_total_ticket_count(self._session, department_id),
            by_department=[
                DepartmentTicketCount(
                    department_code=code,
                    department_name=name,
                    count=count,
                )
                for code, name, count in get_ticket_counts_by_department(
                    self._session,
                    department_id,
                )
            ],
            by_status=[
                TicketDimensionCount(value=status, count=count)
                for status, count in get_ticket_counts_by_status(
                    self._session,
                    department_id,
                )
            ],
            by_language=[
                TicketDimensionCount(value=language, count=count)
                for language, count in get_ticket_counts_by_language(
                    self._session,
                    department_id,
                )
            ],
            average_resolution_time_hours=(
                sum(durations_hours) / len(durations_hours) if durations_hours else None
            ),
        )

    @staticmethod
    def _department_scope(officer: Officer) -> int | None:
        """Return global admin scope or require an officer department."""
        if officer.role == "ADMIN":
            return None
        if officer.role == "DEPARTMENT_OFFICER" and officer.department_id is not None:
            return officer.department_id
        raise DomainError(
            code="FORBIDDEN",
            message="This account is not authorized for analytics",
            status_code=403,
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Normalize SQLite's naive timestamps to UTC before subtracting."""
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
