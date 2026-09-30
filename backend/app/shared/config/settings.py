"""Typed application settings loaded from environment variables."""

import json
from functools import lru_cache
from typing import Annotated, Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Secrets come only from the environment (.env is not committed)."""

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
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    # Data: "firebase" (Firestore) or "memory" (process-local, for tests).
    persistence_backend: Literal["firebase", "memory"] = "firebase"
    # Original files: "local" (folder on the API machine, free) or "firebase" (Storage, Blaze plan).
    storage_backend: Literal["local", "firebase"] = "local"
    local_storage_dir: str = ".data/uploads"

    # Identity: "firebase" (anonymous Firebase Auth ID tokens) or "fake" (`Bearer dev-<uid>`,
    # local development and tests only; refused in production).
    auth_backend: Literal["firebase", "fake"] = "firebase"
    # Tolerance for small clock differences when checking token timestamps.
    auth_clock_skew_seconds: int = Field(default=10, ge=0, le=60)

    # LGPD retention: every policy is deleted this many hours after upload (no renewal).
    retention_hours: int = Field(default=24, ge=1, le=24 * 30)
    retention_sweep_minutes: int = Field(default=15, ge=1, le=24 * 60)

    # Per-owner quotas (HTTP 429 QUOTA_EXCEEDED). Rate windows live in process memory.
    max_active_policies_per_owner: int = Field(default=20, ge=1, le=1000)
    uploads_per_hour: int = Field(default=10, ge=1, le=1000)
    comparisons_per_hour: int = Field(default=20, ge=1, le=1000)

    firebase_credentials_path: str | None = None
    firebase_project_id: str | None = None
    firebase_client_email: str | None = None
    firebase_private_key: str | None = None
    firebase_storage_bucket: str | None = None

    # AI provider: "gemini" (default, needs GEMINI_API_KEY) or "local" (deterministic
    # stand-in for development without external services; refused in production).
    ai_provider: Literal["gemini", "local"] = "gemini"

    # Gemini 3.5 Flash Lite: extraction, OCR, concept assessment and conclusion (ADR-006, ADR-023).
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"

    # Concepts per assessment call (P-ASSESS-001).
    assessment_batch_size: int = Field(default=10, ge=1, le=31)

    # Native-text pages sent per extraction call; longer documents are read in ranges.
    extraction_pages_per_call: int = Field(default=30, ge=1, le=200)

    ai_timeout_seconds: float = 120.0
    ai_max_attempts: int = Field(default=3, ge=1, le=5)

    max_upload_mb: int = Field(default=20, ge=1, le=100)
    max_files_per_policy: int = Field(default=10, ge=1, le=30)
    worker_concurrency: int = Field(default=2, ge=1, le=8)

    # Decision parameters still PENDING_BUSINESS_VALIDATION (knowledge base, section 10).
    profile_multiplier: float = 1.5
    close_score_threshold: float = 0.03
    min_completeness: float = 0.70
    min_evidence_confidence: float = 0.70

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return [str(origin).strip() for origin in json.loads(stripped)]
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return []

    @field_validator("firebase_private_key", mode="after")
    @classmethod
    def restore_newlines(cls, value: str | None) -> str | None:
        return value.replace("\\n", "\n") if value else value

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")

    @property
    def uses_firebase(self) -> bool:
        return "firebase" in (self.persistence_backend, self.storage_backend, self.auth_backend)

    def missing_required(self) -> list[str]:
        """Names of the variables the configured runtime still needs."""

        missing: list[str] = []
        if self.ai_provider == "gemini" and not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        if self.ai_provider == "local" and self.is_production:
            missing.append("AI_PROVIDER diferente de local (não permitido em produção)")
        if self.auth_backend == "fake" and self.is_production:
            missing.append("AUTH_BACKEND diferente de fake (não permitido em produção)")
        if self.storage_backend == "firebase" and not self.firebase_storage_bucket:
            missing.append("FIREBASE_STORAGE_BUCKET")
        if self.uses_firebase:
            has_file = bool(self.firebase_credentials_path)
            has_fields = all(
                (self.firebase_project_id, self.firebase_client_email, self.firebase_private_key)
            )
            if not (has_file or has_fields):
                missing.append(
                    "FIREBASE_CREDENTIALS_PATH (ou FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL "
                    "e FIREBASE_PRIVATE_KEY)"
                )
        return missing


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""

    return Settings()
