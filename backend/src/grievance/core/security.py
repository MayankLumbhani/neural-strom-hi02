"""Password hashing helpers."""

import bcrypt

MIN_PASSWORD_BYTES = 12
MAX_PASSWORD_BYTES = 72
BCRYPT_ROUNDS = 12


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
