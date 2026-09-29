from app.shared.config.settings import Settings


def test_settings_parse_comma_separated_cors_origins() -> None:
    settings = Settings(
        _env_file=None,
        cors_allowed_origins="http://localhost:5173, http://localhost:4173",
    )

    assert settings.cors_allowed_origins == [
        "http://localhost:5173",
        "http://localhost:4173",
    ]


def test_settings_have_safe_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.firebase_project_id is None
    assert settings.gemini_api_key is None


def test_local_storage_does_not_require_firebase_bucket() -> None:
    settings = Settings(
        _env_file=None,
        gemini_api_key="g",
        groq_api_key="q",
        firebase_credentials_path="conta.json",
    )

    assert settings.storage_backend == "local"
    assert settings.missing_required() == []


def test_firebase_storage_requires_bucket() -> None:
    settings = Settings(
        _env_file=None,
        gemini_api_key="g",
        groq_api_key="q",
        firebase_credentials_path="conta.json",
        storage_backend="firebase",
    )

    assert settings.missing_required() == ["FIREBASE_STORAGE_BUCKET"]


def test_memory_mode_needs_no_firebase_credentials() -> None:
    settings = Settings(
        _env_file=None, gemini_api_key="g", groq_api_key="q", persistence_backend="memory"
    )

    assert settings.missing_required() == []
