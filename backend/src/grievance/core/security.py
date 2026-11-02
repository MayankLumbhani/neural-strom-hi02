"""Password hashing helpers."""

import base64
import binascii
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import cast

import bcrypt

MIN_PASSWORD_BYTES = 12
MAX_PASSWORD_BYTES = 72
BCRYPT_ROUNDS = 12


def _encode_segment(value: dict[str, str | int]) -> str:
    """Encode a JWT JSON segment without URL-unsafe characters or padding."""
    encoded = base64.urlsafe_b64encode(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    return encoded.rstrip(b"=").decode("ascii")


def create_access_token(subject: str, secret: str, expires_minutes: int) -> str:
    """Create an HS256 JWT with a subject and expiration timestamp."""
    now = datetime.now(UTC)
    header = _encode_segment({"alg": "HS256", "typ": "JWT"})
    payload = _encode_segment(
        {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        }
    )
    unsigned_token = f"{header}.{payload}"
    signature = hmac.new(
        secret.encode("utf-8"),
        unsigned_token.encode("ascii"),
        hashlib.sha256,
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{unsigned_token}.{encoded_signature}"


def _decode_segment(segment: str) -> dict[str, object]:
    """Decode a JWT JSON object, rejecting malformed base64 and non-object values."""
    try:
        decoded = base64.b64decode(
            segment + "=" * (-len(segment) % 4),
            altchars=b"-_",
            validate=True,
        )
        value = json.loads(decoded)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("Malformed access token") from error
    if not isinstance(value, dict):
        raise ValueError("Malformed access token")
    return cast(dict[str, object], value)


def decode_access_token(token: str, secret: str) -> str:
    """Verify an HS256 JWT and return its subject if it has not expired."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed access token")

    header = _decode_segment(parts[0])
    if header != {"alg": "HS256", "typ": "JWT"}:
        raise ValueError("Unsupported access token")

    unsigned_token = f"{parts[0]}.{parts[1]}"
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        unsigned_token.encode("ascii"),
        hashlib.sha256,
    ).digest()
    try:
        supplied_signature = base64.b64decode(
            parts[2] + "=" * (-len(parts[2]) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError) as error:
        raise ValueError("Malformed access token") from error
    if not hmac.compare_digest(supplied_signature, expected_signature):
        raise ValueError("Invalid access token signature")

    payload = _decode_segment(parts[1])
    subject = payload.get("sub")
    expires_at = payload.get("exp")
    if (
        not isinstance(subject, str)
        or not subject
        or not isinstance(expires_at, int)
        or isinstance(expires_at, bool)
        or expires_at <= int(datetime.now(UTC).timestamp())
    ):
        raise ValueError("Invalid or expired access token")
    return subject


def validate_password(password: str) -> None:
    """Reject passwords outside bcrypt's supported safe byte range."""
    password_bytes = password.encode("utf-8")
    if not MIN_PASSWORD_BYTES <= len(password_bytes) <= MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Passwords must be between {MIN_PASSWORD_BYTES} and {MAX_PASSWORD_BYTES} UTF-8 bytes"
        )


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    validate_password(password)
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(password_bytes, password_hash.encode("ascii"))
