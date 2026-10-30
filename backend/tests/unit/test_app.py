"""Tests for application setup."""

from fastapi.testclient import TestClient

from grievance.app import create_app


def test_app_factory_exposes_openapi_schema() -> None:
    """Verify the application factory creates a usable FastAPI app."""
    response = TestClient(create_app()).get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Neural Storm Grievance API"
