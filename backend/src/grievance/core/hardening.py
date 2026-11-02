"""Public endpoint rate limiting and response security headers."""

import math
import re
import threading
from collections import deque
from dataclasses import dataclass
from time import monotonic

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from grievance.core.config import Settings
from grievance.schemas.errors import ErrorDetail, ErrorResponse

_RATE_PATTERN = re.compile(r"^(?P<count>[1-9][0-9]*)/(?P<unit>second|minute|hour|day)s?$")
_UNIT_SECONDS = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
}


@dataclass(frozen=True)
class RateRule:
    """Request allowance over a fixed sliding-window duration."""

    count: int
    window_seconds: int


@dataclass
class _RateWindow:
    """Recent request timestamps for one client and endpoint."""

    rule: RateRule
    timestamps: deque[float]


def parse_rate_rule(value: str) -> RateRule:
    """Parse a positive request limit such as `10/minute`."""
    match = _RATE_PATTERN.fullmatch(value.strip().casefold())
    if match is None:
        raise ValueError(
            "Rate limits must use a positive count and one of second, minute, hour, or day"
        )
    unit = match.group("unit")
    return RateRule(
        count=int(match.group("count")),
        window_seconds=_UNIT_SECONDS[unit],
    )


class PublicRateLimiter:
    """Track sliding-window request counts in this API process."""

    def __init__(self, settings: Settings) -> None:
        """Parse configured per-endpoint limits and initialize transient counters."""
        self._rules = {
            "chat": parse_rate_rule(settings.rate_limit_chat),
            "status": parse_rate_rule(settings.rate_limit_status),
        }
        self._windows: dict[tuple[str, str], _RateWindow] = {}
        self._next_cleanup_at = 0.0
        self._lock = threading.Lock()

    def retry_after(
        self,
        method: str,
        path: str,
        client_ip: str,
        now: float | None = None,
    ) -> int | None:
        """Return retry seconds when the client exceeds a configured public limit."""
        endpoint = self._endpoint_key(method, path)
        if endpoint is None:
            return None

        current_time = monotonic() if now is None else now
        rule = self._rules[endpoint]
        key = (client_ip, endpoint)
        with self._lock:
            self._cleanup(current_time)
            window = self._windows.get(key)
            if window is None:
                window = _RateWindow(rule=rule, timestamps=deque())
                self._windows[key] = window

            cutoff = current_time - rule.window_seconds
            while window.timestamps and window.timestamps[0] <= cutoff:
                window.timestamps.popleft()
            if len(window.timestamps) >= rule.count:
                return max(1, math.ceil(window.timestamps[0] + rule.window_seconds - current_time))
            window.timestamps.append(current_time)
            return None

    def _cleanup(self, now: float) -> None:
        """Discard expired client windows periodically to bound stale state."""
        cleanup_interval = min(rule.window_seconds for rule in self._rules.values())
        if now < self._next_cleanup_at:
            return
        for key, window in list(self._windows.items()):
            cutoff = now - window.rule.window_seconds
            while window.timestamps and window.timestamps[0] <= cutoff:
                window.timestamps.popleft()
            if not window.timestamps:
                del self._windows[key]
        self._next_cleanup_at = now + cleanup_interval

    @staticmethod
    def _endpoint_key(method: str, path: str) -> str | None:
        """Identify public routes subject to configured per-IP quotas."""
        if method == "POST" and path == "/api/v1/chat/messages":
            return "chat"
        ticket_prefix = "/api/v1/tickets/"
        public_id = path.removeprefix(ticket_prefix)
        if (
            method == "GET"
            and path.startswith(ticket_prefix)
            and public_id
            and "/" not in public_id
        ):
            return "status"
        return None


class PublicHardeningMiddleware(BaseHTTPMiddleware):
    """Limit public traffic and add conservative browser security headers."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        """Create a process-local rate limiter from validated runtime settings."""
        super().__init__(app)
        self._limiter = PublicRateLimiter(settings)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Apply route quotas and security headers without logging request content."""
        client_ip = request.client.host if request.client is not None else "unknown"
        retry_after = self._limiter.retry_after(
            request.method,
            request.url.path,
            client_ip,
        )
        response: Response
        if retry_after is not None:
            request_id = str(getattr(request.state, "request_id", ""))
            response = JSONResponse(
                status_code=429,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="RATE_LIMIT_EXCEEDED",
                        message="Too many requests",
                        details={},
                    ),
                    request_id=request_id,
                ).model_dump(mode="json"),
                headers={"Retry-After": str(retry_after)},
            )
        else:
            response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=()"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
