"""Tests for application setup."""

from fastapi.testclient import TestClient

from grievance.app import create_app


def test_health_endpoints_report_liveness_and_unknown_dependencies() -> None:
    """Verify health and readiness responses before dependencies are implemented."""
    client = TestClient(create_app())

    health_response = client.get("/health")
    readiness_response = client.get("/ready")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert readiness_response.status_code == 200
    assert readiness_response.json() == {
        "status": "ready",
        "db": "unknown",
        "model": "unknown",
    }
