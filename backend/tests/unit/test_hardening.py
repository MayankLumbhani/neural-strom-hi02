"""Tests for public request-rate rules and client isolation."""

import pytest

from grievance.core.config import Settings
from grievance.core.hardening import PublicRateLimiter, RateRule, parse_rate_rule


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("10/minute", RateRule(count=10, window_seconds=60)),
        ("2/seconds", RateRule(count=2, window_seconds=1)),
        ("3/hour", RateRule(count=3, window_seconds=3600)),
    ],
)
def test_parse_rate_rule(value: str, expected: RateRule) -> None:
    """Parse configured count and time unit into a sliding-window rule."""
    assert parse_rate_rule(value) == expected


@pytest.mark.parametrize("value", ["0/minute", "-1/minute", "ten/minute", "10/month"])
def test_parse_rate_rule_rejects_invalid_values(value: str) -> None:
    """Fail clearly instead of silently disabling invalid rate settings."""
    with pytest.raises(ValueError, match="Rate limits must use a positive count"):
        parse_rate_rule(value)


def test_limiter_tracks_clients_and_endpoints_independently() -> None:
    """Keep per-IP chat and status quotas isolated from other client addresses."""
    limiter = PublicRateLimiter(
        Settings(
            _env_file=None,
            rate_limit_chat="2/minute",
            rate_limit_status="1/minute",
        )
    )

    assert limiter.retry_after("POST", "/api/v1/chat/messages", "192.0.2.1", now=10) is None
    assert limiter.retry_after("POST", "/api/v1/chat/messages", "192.0.2.1", now=11) is None
    assert limiter.retry_after("POST", "/api/v1/chat/messages", "192.0.2.1", now=12) == 58
    assert limiter.retry_after("POST", "/api/v1/chat/messages", "192.0.2.2", now=12) is None
    assert limiter.retry_after("GET", "/api/v1/tickets/FMC-TEST", "192.0.2.1", now=12) is None
    assert limiter.retry_after("GET", "/api/v1/tickets/FMC-TEST", "192.0.2.1", now=13) == 59


def test_limiter_uses_sliding_window_and_ignores_non_public_routes() -> None:
    """Release quota as individual hits expire and bypass unconfigured endpoints."""
    limiter = PublicRateLimiter(Settings(_env_file=None, rate_limit_chat="1/second"))

    assert limiter.retry_after("POST", "/api/v1/chat/messages", "192.0.2.1", now=10) is None
    assert limiter.retry_after("POST", "/api/v1/chat/messages", "192.0.2.1", now=10.5) == 1
    assert limiter.retry_after("POST", "/api/v1/chat/messages", "192.0.2.1", now=11) is None
    assert limiter.retry_after("GET", "/api/v1/admin/tickets", "192.0.2.1", now=11) is None
