"""Every /api/v1 route requires a bearer token; /health stays public."""

from pathlib import Path

import pytest
from app.domain.interfaces.ports import Identity
from app.shared.exceptions import InfrastructureError
from fastapi.testclient import TestClient

from tests.fakes import auth_headers, build_test_app

ROUTES = [
    ("GET", "/api/v1/policies"),
    ("POST", "/api/v1/policies"),
    ("GET", "/api/v1/policies/pol_x"),
    ("DELETE", "/api/v1/policies/pol_x"),
    ("POST", "/api/v1/policies/pol_x/cancel"),
    ("GET", "/api/v1/comparisons"),
    ("POST", "/api/v1/comparisons"),
    ("GET", "/api/v1/comparisons/cmp_x"),
    ("GET", "/api/v1/concepts"),
    ("GET", "/api/v1/concepts/DO-015"),
    ("GET", "/api/v1/concepts/DO-015/occurrences"),
    ("POST", "/api/v1/queries"),
    ("GET", "/api/v1/me/data/summary"),
    ("DELETE", "/api/v1/me/data"),
]

BAD_HEADERS = [
    ({}, "AUTH_REQUIRED"),
    ({"Authorization": ""}, "AUTH_REQUIRED"),
    ({"Authorization": "Basic dXNlcjpwYXNz"}, "AUTH_REQUIRED"),
    ({"Authorization": "Bearer"}, "AUTH_REQUIRED"),
    ({"Authorization": "Bearer a b"}, "AUTH_REQUIRED"),
    ({"Authorization": "Bearer token-forjado"}, "AUTH_TOKEN_INVALID"),
]


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory) -> TestClient:
    return TestClient(build_test_app(tmp_path_factory.mktemp("auth")))


@pytest.mark.parametrize(("method", "url"), ROUTES)
@pytest.mark.parametrize(("headers", "code"), BAD_HEADERS)
def test_routes_reject_requests_without_a_valid_token(
    client: TestClient, method: str, url: str, headers: dict[str, str], code: str
) -> None:
    response = client.request(method, url, headers=headers)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    error = response.json()["error"]
    assert error["code"] == code
    assert error["message"]
    assert set(error) == {"code", "message", "correlation_id", "details"}


def test_health_is_public(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_valid_token_is_accepted(client: TestClient) -> None:
    assert client.get("/api/v1/policies", headers=auth_headers()).status_code == 200


def test_revoked_token_is_refused_only_where_revocation_is_checked(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)
    app.state.runtime.identity.revoked.add("alice")
    with TestClient(app, headers=auth_headers("alice")) as client:
        assert client.get("/api/v1/me/data/summary").status_code == 200
        response = client.delete("/api/v1/me/data")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_TOKEN_REVOKED"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_identity_provider_outage_is_a_503_without_details(tmp_path: Path) -> None:
    class Unavailable:
        async def verify(self, token: str, check_revoked: bool = False) -> Identity:
            raise InfrastructureError(
                "Não foi possível confirmar seu acesso agora.",
                code="AUTH_UNAVAILABLE",
                details={"retryable": True},
            )

    app = build_test_app(tmp_path)
    app.state.identity_verifier = Unavailable()
    with TestClient(app) as client:
        response = client.get("/api/v1/policies", headers=auth_headers())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_UNAVAILABLE"
