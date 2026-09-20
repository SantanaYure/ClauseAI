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
