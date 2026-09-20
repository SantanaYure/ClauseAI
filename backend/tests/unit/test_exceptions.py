from app.infrastructure.events import InMemoryEventBus
from app.presentation.api.app import create_app
from app.shared.config.settings import Settings
from app.shared.exceptions import ValidationError
from fastapi import APIRouter
from fastapi.testclient import TestClient


def test_known_exception_uses_standard_error_envelope() -> None:
    app = create_app(Settings(_env_file=None), InMemoryEventBus())
    router = APIRouter()

    @router.get("/test-validation-error")
    async def raise_validation_error() -> None:
        raise ValidationError("Invalid test input", code="TEST_INVALID")

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/test-validation-error", headers={"X-Correlation-ID": "cor-test"})

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "TEST_INVALID",
            "message": "Invalid test input",
            "correlation_id": "cor-test",
            "details": None,
        }
    }
    assert response.headers["X-Correlation-ID"] == "cor-test"
