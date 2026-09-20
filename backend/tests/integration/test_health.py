from app.infrastructure.events import InMemoryEventBus
from app.presentation.api.app import create_app
from app.shared.config.settings import Settings
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok() -> None:
    app = create_app(Settings(_env_file=None), InMemoryEventBus())
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Correlation-ID"]
