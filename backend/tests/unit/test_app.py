"""Tests for application setup."""

from uuid import UUID

from fastapi.testclient import TestClient

from grievance.app import create_app
from grievance.core.config import Settings
from grievance.core.exceptions import DomainError


def test_health_endpoints_report_liveness_and_unknown_dependencies() -> None:
    """Verify health and readiness responses before dependencies are implemented."""
    client = TestClient(create_app())

    health_response = client.get("/health")
    readiness_response = client.get("/ready")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert health_response.headers["x-request-id"]
    assert readiness_response.status_code == 200
    assert readiness_response.json() == {
        "status": "ready",
        "db": "unknown",
        "model": "unknown",
    }


def test_domain_errors_use_standard_response_and_request_id() -> None:
    """Verify domain exceptions return the standard body and correlate by request ID."""
    app = create_app(Settings(_env_file=None, app_env="test"))

    @app.get("/test-domain-error")
    def raise_domain_error() -> None:
        raise DomainError(
            code="INVALID_TRANSITION",
            message="Invalid status transition",
            status_code=409,
            details={"current_status": "RESOLVED"},
        )

    request_id = "12345678-1234-5678-1234-567812345678"
    response = TestClient(app).get(
        "/test-domain-error",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 409
    assert response.headers["x-request-id"] == request_id
    assert response.json() == {
        "error": {
            "code": "INVALID_TRANSITION",
            "message": "Invalid status transition",
            "details": {"current_status": "RESOLVED"},
        },
        "request_id": request_id,
    }


def test_invalid_request_id_is_replaced_with_uuid() -> None:
    """Replace malformed request ID headers instead of returning them to callers."""
    response = TestClient(create_app(Settings(_env_file=None))).get(
        "/health",
        headers={"X-Request-ID": "not-a-uuid"},
    )

    assert response.status_code == 200
    assert str(UUID(response.headers["x-request-id"])) == response.headers["x-request-id"]
    assert response.headers["x-request-id"] != "not-a-uuid"


def test_unexpected_error_is_generic_and_does_not_expose_exception_text() -> None:
    """Return a safe internal-error response without exposing exception content."""
    app = create_app(Settings(_env_file=None, app_env="test"))

    @app.get("/test-unexpected-error")
    def raise_unexpected_error() -> None:
        raise RuntimeError("synthetic complaint content")

    response = TestClient(app).get("/test-unexpected-error")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "synthetic complaint content" not in response.text
