"""Tests for environment-backed application settings."""

import logging

import pytest
from pydantic import ValidationError

from grievance.core.config import Settings
from grievance.core.database import get_engine
from grievance.core.logging import JsonFormatter


def test_settings_parse_cors_origins_and_keep_secrets_redacted() -> None:
    """Verify comma-separated origins parse and secret values are not exposed."""
    settings = Settings(
        _env_file=None,
        cors_origins="https://one.example, https://two.example",
        jwt_secret="test-secret",
    )

    assert settings.cors_origin_list == ["https://one.example", "https://two.example"]
    assert "test-secret" not in repr(settings)


def test_settings_cover_architecture_environment_variables() -> None:
    """Keep every documented runtime variable represented in application settings."""
    expected = {
        "APP_ENV",
        "LOG_LEVEL",
        "DEMO_MODE",
        "DATABASE_URL",
        "JWT_SECRET",
        "JWT_EXPIRE_MINUTES",
        "CORS_ORIGINS",
        "CLASSIFIER_BACKEND",
        "MODEL_NAME_OR_PATH",
        "HF_TOKEN",
        "CLASSIFIER_HIGH_THRESHOLD",
        "CLASSIFIER_LOW_THRESHOLD",
        "LLM_ENABLED",
        "GEMINI_API_KEY",
        "LLM_TIMEOUT_SECONDS",
        "ESCALATION_INTERVAL_SECONDS",
        "RATE_LIMIT_CHAT",
        "RATE_LIMIT_STATUS",
        "MAX_MESSAGE_LENGTH",
        "DEMO_OFFICER_USERNAME",
        "DEMO_OFFICER_PASSWORD",
        "DEMO_OFFICER_DEPARTMENT_CODE",
        "DEMO_ADMIN_USERNAME",
        "DEMO_ADMIN_PASSWORD",
    }

    assert {field.upper() for field in Settings.model_fields} == expected


def test_settings_reject_inverted_confidence_thresholds() -> None:
    """Require the low classifier threshold to remain below the high threshold."""
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            classifier_low_threshold=0.8,
            classifier_high_threshold=0.7,
        )


def test_database_engine_requires_configured_url() -> None:
    """Fail explicitly when a session is requested without DATABASE_URL."""
    with pytest.raises(RuntimeError, match="DATABASE_URL must be configured"):
        get_engine(Settings(_env_file=None))


def test_json_formatter_omits_unapproved_record_fields() -> None:
    """Keep complaint text out of structured log output."""
    record = logging.LogRecord(
        name="grievance",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request.completed",
        args=(),
        exc_info=None,
    )
    record.complaint_text = "synthetic complaint content"

    formatted = JsonFormatter().format(record)

    assert "request.completed" in formatted
    assert "synthetic complaint content" not in formatted
