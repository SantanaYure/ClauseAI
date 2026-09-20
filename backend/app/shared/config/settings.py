"""Typed application settings loaded from environment variables."""

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API foundation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "ClauseAI API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    firebase_project_id: str | None = None
    firebase_client_email: str | None = None
    firebase_private_key: str | None = None
    firebase_storage_bucket: str | None = None

    gemini_api_key: str | None = None
    groq_api_key: str | None = None

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""

    return Settings()
