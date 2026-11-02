"""Authentication request and response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Credentials for an officer or administrator login."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    """Signed access token and authenticated account summary."""

    access_token: str
    token_type: str = "bearer"
    role: str
    department: str | None
