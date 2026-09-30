"""CORS, security headers, correlation id and production-only switches."""

from pathlib import Path

import pytest
from app.main import ConfigurationError, build_application
from app.shared.config.settings import Settings
from fastapi.testclient import TestClient

from tests.fakes import auth_headers, build_test_app

ORIGIN = "http://localhost:5173"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "persistence_backend": "memory",
        "auth_backend": "fake",
        "cors_allowed_origins": ORIGIN,
    }
    return Settings(_env_file=None, **{**values, **overrides})  # type: ignore[arg-type]


def test_cors_allows_only_configured_origins_without_credentials(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path, settings=_settings())) as client:
        preflight = client.options(
            "/api/v1/policies",
            headers={
                "Origin": ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,x-correlation-id",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == ORIGIN
        assert "access-control-allow-credentials" not in preflight.headers
        allowed = preflight.headers["access-control-allow-headers"].lower()
        assert "authorization" in allowed and "x-correlation-id" in allowed

        response = client.get("/api/v1/policies", headers={"Origin": ORIGIN, **auth_headers()})
        assert response.headers["access-control-expose-headers"] == "X-Correlation-ID"

        evil = client.options(
            "/api/v1/policies",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
        )
        assert "access-control-allow-origin" not in evil.headers


def test_security_headers_and_no_store_on_the_api(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path, settings=_settings())) as client:
        api = client.get("/api/v1/policies", headers=auth_headers())
        health = client.get("/health")
        unauthorized = client.get("/api/v1/policies")

    for response in (api, health, unauthorized):
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Referrer-Policy"] == "no-referrer"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" not in response.headers
    assert api.headers["Cache-Control"] == "no-store"
    assert unauthorized.headers["Cache-Control"] == "no-store"
    assert "no-store" not in health.headers.get("Cache-Control", "")


def test_production_adds_hsts_and_hides_the_docs(tmp_path: Path) -> None:
    development = build_test_app(tmp_path, settings=_settings())
    production = build_test_app(tmp_path, settings=_settings(app_env="production"))
    with TestClient(development) as client:
        assert client.get("/api/v1/openapi.json").status_code == 200
    with TestClient(production) as client:
        assert "max-age" in client.get("/health").headers["Strict-Transport-Security"]
        for url in ("/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json"):
            assert client.get(url).status_code == 404


@pytest.mark.parametrize(
    ("received", "echoed"),
    [("abc-123", True), ("x" * 64, True), ("x" * 65, False), ("a<script>", False), ("", False)],
)
def test_correlation_id_is_validated(tmp_path: Path, received: str, echoed: bool) -> None:
    with TestClient(build_test_app(tmp_path)) as client:
        response = client.get("/health", headers={"X-Correlation-ID": received})
    returned = response.headers["X-Correlation-ID"]
    assert (returned == received) is echoed
    assert returned


def test_fake_identity_is_refused_in_production(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        auth_backend="fake",
        ai_provider="gemini",
        gemini_api_key="g",
        firebase_credentials_path="conta.json",
    )
    assert any("AUTH_BACKEND" in item for item in settings.missing_required())
    with pytest.raises(ConfigurationError, match="AUTH_BACKEND"):
        build_application(settings)


def test_local_development_runs_with_fake_identity_and_memory(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        ai_provider="local",
        auth_backend="fake",
        persistence_backend="memory",
        storage_backend="local",
        local_storage_dir=str(tmp_path),
    )
    assert settings.missing_required() == []
    with TestClient(build_application(settings), headers=auth_headers()) as client:
        assert client.get("/api/v1/policies").json() == {"items": [], "next_cursor": None}


def test_firebase_identity_requires_credentials() -> None:
    settings = Settings(_env_file=None, gemini_api_key="g", persistence_backend="memory")
    assert settings.auth_backend == "firebase"
    assert any("FIREBASE_CREDENTIALS_PATH" in item for item in settings.missing_required())


def test_api_without_bearer_is_refused_with_cors_and_envelope(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path, settings=_settings())) as client:
        for headers in ({}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer  "}):
            response = client.post(
                "/api/v1/policies",
                headers={"Origin": ORIGIN, "X-Correlation-ID": "abc-123", **headers},
                files=[("files", ("a.pdf", b"%PDF-1.4", "application/pdf"))],
            )
            assert response.status_code == 401
            assert response.headers["WWW-Authenticate"] == "Bearer"
            assert response.headers["access-control-allow-origin"] == ORIGIN
            assert response.headers["X-Correlation-ID"] == "abc-123"
            error = response.json()["error"]
            assert (error["code"], error["correlation_id"]) == ("AUTH_REQUIRED", "abc-123")

        preflight = client.options(
            "/api/v1/policies",
            headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"},
        )
        assert preflight.status_code == 200
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/openapi.json").status_code == 200


def test_oversized_upload_is_refused_by_content_length(tmp_path: Path) -> None:
    settings = _settings(max_files_per_policy=1, max_upload_mb=1)
    with TestClient(build_test_app(tmp_path, settings=settings), headers=auth_headers()) as client:
        response = client.post(
            "/api/v1/policies",
            headers={"Origin": ORIGIN},
            files=[("files", ("a.pdf", b"%PDF" + b"0" * (3 * 1024 * 1024), "application/pdf"))],
        )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert response.headers["access-control-allow-origin"] == ORIGIN


async def test_refusal_happens_before_the_body_is_read(tmp_path: Path) -> None:
    app = build_test_app(tmp_path, settings=_settings())
    body_reads: list[int] = []
    sent: list[dict[str, object]] = []

    async def receive() -> dict[str, object]:
        body_reads.append(1)
        return {"type": "http.request", "body": b"x" * 1024, "more_body": False}

    async def send(message: dict[str, object]) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/policies",
        "raw_path": b"/api/v1/policies",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"content-type", b"multipart/form-data; boundary=x")],
        "client": ("127.0.0.1", 1),
        "server": ("testserver", 80),
    }
    await app(scope, receive, send)

    assert sent[0]["status"] == 401
    assert body_reads == []
