"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    demo_mode: bool = True
    database_url: SecretStr | None = None
    jwt_secret: SecretStr | None = None
    jwt_expire_minutes: int = Field(default=60, gt=0)
    cors_origins: str = ""
    classifier_backend: Literal["muril", "onnx", "baseline"] = "baseline"
    model_name_or_path: str | None = None
    hf_token: SecretStr | None = None
    classifier_high_threshold: float = Field(default=0.75, gt=0, le=1)
    classifier_low_threshold: float = Field(default=0.45, gt=0, le=1)
    llm_enabled: bool = False
    gemini_api_key: SecretStr | None = None
    gemini_model: str | None = None
    llm_timeout_seconds: float = Field(default=60, gt=0)
    dataset_seed: int = 20261031
    dataset_tier1_samples_per_class_language: int = Field(default=100, ge=2)
    dataset_tier2_samples_per_class_language: int = Field(default=30, ge=2)
    dataset_minimum_stratum_fraction: float = Field(default=0.9, gt=0, le=1)
    escalation_interval_seconds: int = Field(default=60, gt=0)
    rate_limit_chat: str = "10/minute"
    rate_limit_status: str = "30/minute"
    max_message_length: int = Field(default=2000, gt=0)
    demo_officer_username: str | None = Field(default=None, max_length=100)
    demo_officer_password: SecretStr | None = None
    demo_officer_department_code: str = Field(default="WATER", max_length=50)
    demo_admin_username: str | None = Field(default=None, max_length=100)
    demo_admin_password: SecretStr | None = None

    @model_validator(mode="after")
    def validate_confidence_thresholds(self) -> "Settings":
        """Require the low confidence threshold to be lower than the high threshold."""
        if self.classifier_low_threshold >= self.classifier_high_threshold:
            raise ValueError("CLASSIFIER_LOW_THRESHOLD must be less than CLASSIFIER_HIGH_THRESHOLD")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        """Return configured CORS origins as a trimmed list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
