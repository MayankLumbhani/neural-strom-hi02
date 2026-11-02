"""HTTP integration tests for authentication and department-scoped tickets."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from grievance.app import create_app
from grievance.core.config import Settings
from grievance.core.database import get_session
from grievance.core.security import hash_password
from grievance.models import Conversation, Department, Officer, Ticket, TicketEvent
from grievance.nlp.classifier import FakeClassifier
from grievance.seed import DEPARTMENTS
from grievance.services.ticket_service import TicketService

OFFICER_PASSWORD = "synthetic-officer-password"
ADMIN_PASSWORD = "synthetic-admin-password"


@pytest.fixture
def admin_api() -> Generator[tuple[TestClient, Engine, Settings], None, None]:
    """Provide an isolated API with two departments and staff accounts."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        departments = [
            Department(
                code=seed.code,
                name_en=seed.name_en,
                name_hi=seed.name_hi,
                name_gu=seed.name_gu,
                sla_hours=seed.sla_hours,
            )
            for seed in DEPARTMENTS
        ]
        session.add_all(departments)
        session.flush()
        water = session.exec(select(Department).where(Department.code == "WATER")).one()
        session.add_all(
            [
                Officer(
                    username="water-officer",
                    password_hash=hash_password(OFFICER_PASSWORD),
                    role="DEPARTMENT_OFFICER",
                    department_id=water.id,
                ),
                Officer(
                    username="administrator",
                    password_hash=hash_password(ADMIN_PASSWORD),
                    role="ADMIN",
                ),
            ]
        )
        session.commit()

    def override_session() -> Generator[Session, None, None]:
        """Use the isolated database and commit successful requests."""
        with Session(engine) as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise
            else:
                session.commit()

    settings = Settings(
        _env_file=None,
        app_env="test",
        jwt_secret="test-only-signing-secret",
    )
    app = create_app(settings, classifier=FakeClassifier("WATER"))
    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, engine, settings
    app.dependency_overrides.clear()
    engine.dispose()


def _create_ticket(engine: Engine, department_code: str) -> str:
    """Create one synthetic ticket and return its public ID."""
    with Session(engine) as session:
        department = session.exec(
            select(Department).where(Department.code == department_code)
        ).one()
        conversation = Conversation(language="en")
        session.add(conversation)
        session.flush()
        ticket = TicketService(session, Settings(_env_file=None)).create_ticket(
            conversation_id=conversation.id,
            department_id=department.id,
            complaint_text=f"Synthetic {department_code} complaint",
            language="en",
            location_text="Ward 4",
        )
        session.commit()
        return ticket.public_id


def _login(client: TestClient, username: str, password: str) -> str:
    """Login a test account and return its access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_issues_role_scoped_token_and_rejects_bad_credentials(
    admin_api: tuple[TestClient, Engine, Settings],
) -> None:
    """Return a bearer token for valid users and a generic error otherwise."""
    client, _, _ = admin_api

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "water-officer", "password": OFFICER_PASSWORD},
    )
    invalid = client.post(
        "/api/v1/auth/login",
        json={"username": "water-officer", "password": "incorrect-password"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["role"] == "DEPARTMENT_OFFICER"
    assert response.json()["department"] == "WATER"
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_admin_routes_require_authentication(
    admin_api: tuple[TestClient, Engine, Settings],
) -> None:
    """Reject requests without a bearer token using the standard error shape."""
    client, _, _ = admin_api

    response = client.get("/api/v1/admin/tickets")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_officer_list_and_detail_are_scoped_to_their_department(
    admin_api: tuple[TestClient, Engine, Settings],
) -> None:
    """Hide tickets assigned to another department from an officer's queue."""
    client, engine, _ = admin_api
    water_id = _create_ticket(engine, "WATER")
    roads_id = _create_ticket(engine, "ROADS")
    token = _login(client, "water-officer", OFFICER_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}

    queue = client.get("/api/v1/admin/tickets?page=1&page_size=1", headers=headers)
    own_ticket = client.get(f"/api/v1/admin/tickets/{water_id}", headers=headers)
    other_ticket = client.get(f"/api/v1/admin/tickets/{roads_id}", headers=headers)

    assert queue.status_code == 200
    assert queue.json()["total"] == 1
    assert [item["public_id"] for item in queue.json()["items"]] == [water_id]
    assert own_ticket.status_code == 200
    assert own_ticket.json()["department"] == "WATER"
    assert other_ticket.status_code == 404
    assert other_ticket.json()["error"]["code"] == "TICKET_NOT_FOUND"


def test_officer_cannot_change_another_departments_ticket(
    admin_api: tuple[TestClient, Engine, Settings],
) -> None:
    """Enforce ticket scope before applying status changes or writing events."""
    client, engine, _ = admin_api
    water_id = _create_ticket(engine, "WATER")
    roads_id = _create_ticket(engine, "ROADS")
    token = _login(client, "water-officer", OFFICER_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}

    forbidden = client.patch(
        f"/api/v1/admin/tickets/{roads_id}/status",
        headers=headers,
        json={"status": "ASSIGNED", "note": "cross-department attempt"},
    )
    allowed = client.patch(
        f"/api/v1/admin/tickets/{water_id}/status",
        headers=headers,
        json={"status": "ASSIGNED", "note": "Officer accepted ticket"},
    )

    with Session(engine) as session:
        roads_ticket = session.exec(select(Ticket).where(Ticket.public_id == roads_id)).one()
        roads_event_notes = session.exec(
            select(TicketEvent.note).where(TicketEvent.ticket_id == roads_ticket.id)
        ).all()

    assert forbidden.status_code == 404
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "ASSIGNED"
    assert allowed.json()["events"][-1]["note"] == "Officer accepted ticket"
    assert roads_ticket.status == "FILED"
    assert roads_event_notes == [None]


def test_admin_can_list_tickets_across_departments(
    admin_api: tuple[TestClient, Engine, Settings],
) -> None:
    """Allow administrators to view the full ticket queue."""
    client, engine, _ = admin_api
    water_id = _create_ticket(engine, "WATER")
    roads_id = _create_ticket(engine, "ROADS")
    token = _login(client, "administrator", ADMIN_PASSWORD)

    response = client.get(
        "/api/v1/admin/tickets",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {item["public_id"] for item in response.json()["items"]} == {water_id, roads_id}


def test_analytics_summary_aggregates_seeded_tickets_and_resolution_time(
    admin_api: tuple[TestClient, Engine, Settings],
) -> None:
    """Report grouped counts and mean resolved duration for admins and officers."""
    client, engine, _ = admin_api
    now = datetime.now(UTC)
    with Session(engine) as session:
        water = session.exec(select(Department).where(Department.code == "WATER")).one()
        roads = session.exec(select(Department).where(Department.code == "ROADS")).one()
        conversations = [Conversation(language=language) for language in ("en", "hi", "gu")]
        session.add_all(conversations)
        session.flush()
        tickets = [
            Ticket(
                public_id="FMC-261102-ANL1",
                conversation_id=conversations[0].id,
                department_id=water.id,
                complaint_text="Synthetic water complaint",
                language="en",
                location_text="Ward 1",
                status="FILED",
                created_at=now - timedelta(hours=4),
                status_changed_at=now - timedelta(hours=4),
            ),
            Ticket(
                public_id="FMC-261102-ANL2",
                conversation_id=conversations[1].id,
                department_id=water.id,
                complaint_text="Synthetic Hindi complaint",
                language="hi",
                location_text="Ward 2",
                status="ASSIGNED",
                created_at=now - timedelta(hours=3),
                status_changed_at=now - timedelta(hours=2),
            ),
            Ticket(
                public_id="FMC-261102-ANL3",
                conversation_id=conversations[2].id,
                department_id=roads.id,
                complaint_text="Synthetic resolved complaint",
                language="gu",
                location_text="Ward 3",
                status="RESOLVED",
                created_at=now - timedelta(hours=2, minutes=30),
                status_changed_at=now,
                resolved_at=now,
            ),
        ]
        session.add_all(tickets)
        session.commit()

    admin_token = _login(client, "administrator", ADMIN_PASSWORD)
    officer_token = _login(client, "water-officer", OFFICER_PASSWORD)
    admin_summary = client.get(
        "/api/v1/admin/analytics/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    officer_summary = client.get(
        "/api/v1/admin/analytics/summary",
        headers={"Authorization": f"Bearer {officer_token}"},
    )

    assert admin_summary.status_code == 200
    admin_body = admin_summary.json()
    assert admin_body["total_tickets"] == 3
    assert {item["department_code"]: item["count"] for item in admin_body["by_department"]} == {
        "ROADS": 1,
        "WATER": 2,
    }
    assert {item["value"]: item["count"] for item in admin_body["by_status"]} == {
        "ASSIGNED": 1,
        "FILED": 1,
        "RESOLVED": 1,
    }
    assert {item["value"]: item["count"] for item in admin_body["by_language"]} == {
        "en": 1,
        "gu": 1,
        "hi": 1,
    }
    assert admin_body["average_resolution_time_hours"] == pytest.approx(2.5)

    assert officer_summary.status_code == 200
    officer_body = officer_summary.json()
    assert officer_body["total_tickets"] == 2
    assert officer_body["by_department"][0]["department_code"] == "WATER"
    assert officer_body["average_resolution_time_hours"] is None
