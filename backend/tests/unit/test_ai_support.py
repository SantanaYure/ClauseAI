import pytest
from app.infrastructure.ai import support
from app.infrastructure.ai.gemini import _normalize
from app.infrastructure.ai.support import (
    InvalidModelOutput,
    RateLimitedError,
    call_with_retries,
    retry_after_seconds,
)
from app.shared.exceptions import InfrastructureError

GROQ_MESSAGE = (
    "Rate limit reached for model `openai/gpt-oss-120b` on tokens per minute (TPM): "
    "Limit 8000, Used 6831, Requested 4882. Please try again in 27.8475s."
)


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        recorded.append(seconds)

    monkeypatch.setattr(support.asyncio, "sleep", fake_sleep)
    return recorded


def test_retry_after_comes_from_header_or_message() -> None:
    assert retry_after_seconds({"retry-after": "12"}, "") == 12
    assert retry_after_seconds({}, GROQ_MESSAGE) == pytest.approx(27.8475)
    assert retry_after_seconds(None, "Please try again in 1m30.5s") == pytest.approx(90.5)
    assert retry_after_seconds(None, "sem indicação") is None


async def test_rate_limit_waits_the_requested_time_without_spending_attempts(
    sleeps: list[float],
) -> None:
    calls = 0

    async def operation() -> str:
        nonlocal calls
        calls += 1
        if calls <= 3:
            raise RateLimitedError(GROQ_MESSAGE, retry_after=27.8)
        return "ok"

    result = await call_with_retries(
        operation, provider="groq", model="m", prompt_version="p", max_attempts=1
    )

    assert result == "ok"
    assert len(sleeps) == 3
    assert all(27.8 <= wait <= 30 for wait in sleeps)


async def test_rate_limit_gives_up_with_a_clear_code(sleeps: list[float]) -> None:
    async def operation() -> str:
        raise RateLimitedError(GROQ_MESSAGE, retry_after=5)

    with pytest.raises(InfrastructureError) as error:
        await call_with_retries(
            operation, provider="groq", model="m", prompt_version="p", max_attempts=3
        )

    assert error.value.code == "MODEL_RATE_LIMITED"
    assert "Aguarde um minuto" in error.value.message


async def test_invalid_output_is_retried_up_to_max_attempts(sleeps: list[float]) -> None:
    async def operation() -> str:
        raise InvalidModelOutput("json inválido")

    with pytest.raises(InfrastructureError) as error:
        await call_with_retries(
            operation, provider="gemini", model="m", prompt_version="p", max_attempts=3
        )

    assert error.value.code == "INVALID_MODEL_OUTPUT"
    assert len(sleeps) == 2


def test_gemini_intake_fields_at_the_root_are_accepted() -> None:
    flat = {"insurer": "Chubb", "document_type": "GENERAL_CONDITIONS", "occurrences": []}

    assert _normalize(flat) == {
        "intake": {"insurer": "Chubb", "document_type": "GENERAL_CONDITIONS"},
        "occurrences": [],
    }
    nested = {"intake": {"insurer": "Chubb"}, "occurrences": []}
    assert _normalize(nested) is nested
