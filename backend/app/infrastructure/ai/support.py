"""Shared AI orchestration helpers: prompts, bounded retries and JSON parsing
(docs/AI_SYSTEM_SPEC.md, sections 3 and 4)."""

import asyncio
import json
import random
import re
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from app.shared.exceptions import InfrastructureError
from app.shared.logging import get_logger, log_context

PROMPTS_DIR = Path(__file__).with_name("prompts")
logger = get_logger("app.ai")


class InvalidModelOutput(Exception):
    """The model answered, but the answer broke the expected schema."""


class TransientProviderError(Exception):
    """Timeout or 5xx: worth retrying."""


class RateLimitedError(TransientProviderError):
    """Provider quota reached (HTTP 429). Retry only after the time it asks for."""

    def __init__(self, message: str, retry_after: float | None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


MAX_RATE_LIMIT_WAIT_SECONDS = 90.0
MAX_RATE_LIMIT_WAITS = 8
_RETRY_IN = re.compile(r"(?:try again|retry) in\s+(?:(\d+)m)?([\d.]+)s", re.IGNORECASE)


def retry_after_seconds(headers: Any, message: str) -> float | None:
    """Wait time from the Retry-After header or from the provider message."""

    header = headers.get("retry-after") if headers is not None else None
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    match = _RETRY_IN.search(message)
    if match:
        return float(match.group(1) or 0) * 60 + float(match.group(2))
    return None


def load_prompt(prompt_id: str) -> str:
    return (PROMPTS_DIR / f"{prompt_id}.md").read_text(encoding="utf-8")


def render(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template


def parse_json_object(text: str | None) -> dict[str, Any]:
    """Parse a JSON object, tolerating a markdown fence around it."""

    if not text:
        raise InvalidModelOutput("Resposta vazia do modelo.")
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise InvalidModelOutput("Resposta do modelo não é JSON válido.") from exc
    if not isinstance(value, dict):
        raise InvalidModelOutput("Resposta do modelo não é um objeto JSON.")
    return value


async def call_with_retries[T](
    operation: Callable[[], Awaitable[T]],
    *,
    provider: str,
    model: str,
    prompt_version: str,
    max_attempts: int,
) -> T:
    """Run an AI call with bounded retries.

    Transient and schema errors use exponential backoff and count as attempts.
    Rate limits (HTTP 429) wait the time the provider asks for and have their own,
    larger budget, so a free-tier quota slows the job down instead of failing it.
    """

    attempt = 0
    rate_limit_waits = 0
    while True:
        started = time.perf_counter()
        try:
            result = await operation()
        except RateLimitedError as exc:
            rate_limit_waits += 1
            wait = min(exc.retry_after or 15.0, MAX_RATE_LIMIT_WAIT_SECONDS)
            with log_context(
                provider=provider,
                model=model,
                rate_limit_wait=str(rate_limit_waits),
                wait_seconds=f"{wait:.1f}",
            ):
                logger.warning("AI rate limit reached; waiting")
            if rate_limit_waits > MAX_RATE_LIMIT_WAITS:
                raise InfrastructureError(
                    f"Limite de uso do provedor de IA ({provider}) atingido. "
                    "Aguarde um minuto e tente novamente.",
                    code="MODEL_RATE_LIMITED",
                    details={"retryable": True},
                ) from exc
            await asyncio.sleep(wait + random.uniform(0.5, 1.5))
            continue
        except (TransientProviderError, InvalidModelOutput) as exc:
            attempt += 1
            with log_context(
                provider=provider,
                model=model,
                attempt=str(attempt),
                error_type=type(exc).__name__,
            ):
                logger.warning("AI call failed")
            if attempt >= max_attempts:
                if isinstance(exc, InvalidModelOutput):
                    raise InfrastructureError(
                        f"O provedor de IA ({provider}) não respondeu no formato esperado.",
                        code="INVALID_MODEL_OUTPUT",
                        details={"retryable": True},
                    ) from exc
                raise InfrastructureError(
                    f"O provedor de IA ({provider}) está indisponível no momento.",
                    code="MODEL_UNAVAILABLE",
                    details={"retryable": True},
                ) from exc
            await asyncio.sleep(2 ** (attempt - 1) + random.uniform(0, 0.5))
            continue
        latency_ms = str(round((time.perf_counter() - started) * 1000))
        with log_context(
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            attempt=str(attempt + 1),
            latency_ms=latency_ms,
        ):
            logger.info("AI call succeeded")
        return result
