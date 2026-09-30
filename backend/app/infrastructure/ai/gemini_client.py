"""Shared Gemini client: one SDK client, JSON responses, error mapping and bounded retries.

Used by every AI step of the pipeline (extraction, concept assessment and executive
conclusion), all on Gemini 3.5 Flash Lite (ADR-006, ADR-023).
"""

from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.infrastructure.ai.support import (
    RateLimitedError,
    TransientProviderError,
    call_with_retries,
    load_prompt,
    parse_json_object,
    retry_after_seconds,
)
from app.shared.exceptions import InfrastructureError

PROVIDER = "gemini"

_AUTH_CODES = {401, 403}


def classify_client_error(exc: genai_errors.ClientError) -> InfrastructureError:
    """Map a provider 4xx to a classified, sanitized error (never the raw provider text)."""

    code = getattr(exc, "code", None)
    invalid_key = "api key" in str(exc).lower()
    if code in _AUTH_CODES or invalid_key:
        return InfrastructureError(
            "A chave de acesso da IA é inválida ou não tem permissão. "
            "Verifique a configuração do backend.",
            code="AI_AUTH_FAILED",
            details={"retryable": False},
        )
    if code == 404:
        return InfrastructureError(
            "O modelo de IA configurado não foi encontrado. Verifique a configuração do backend.",
            code="AI_MODEL_NOT_FOUND",
            details={"retryable": False},
        )
    return InfrastructureError(
        "A IA recusou a requisição (dados em formato não aceito). Tente outro arquivo.",
        code="AI_BAD_REQUEST",
        status_code=502,
        details={"retryable": False},
    )


def _was_truncated(response: types.GenerateContentResponse) -> bool:
    candidates = response.candidates or []
    return bool(candidates) and candidates[0].finish_reason == types.FinishReason.MAX_TOKENS


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_attempts: int,
        assessment_batch_size: int = 10,
    ) -> None:
        self._client = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000))
        )
        self.model = model
        self.max_attempts = max_attempts
        self.assessment_batch_size = assessment_batch_size
        self._system = load_prompt("P-SYSTEM-001")

    async def _generate(self, contents: list[Any]) -> str | None:
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self._system,
                    temperature=0,
                    response_mime_type="application/json",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except (genai_errors.ServerError, httpx.TimeoutException, httpx.TransportError) as exc:
            raise TransientProviderError(str(exc)) from exc
        except genai_errors.ClientError as exc:
            if getattr(exc, "code", None) == 429:
                raise RateLimitedError(str(exc), retry_after_seconds(None, str(exc))) from exc
            if getattr(exc, "code", None) == 408:
                raise TransientProviderError(str(exc)) from exc
            raise classify_client_error(exc) from exc
        if _was_truncated(response):
            raise InfrastructureError(
                "A resposta da IA foi cortada por exceder o tamanho máximo. "
                "O documento é grande demais para uma única leitura; divida-o em partes menores.",
                code="AI_OUTPUT_TRUNCATED",
                status_code=422,
                details={"retryable": False},
            )
        text: str | None = response.text
        return text

    async def with_retries[T](
        self, operation: Callable[[], Awaitable[T]], prompt_version: str
    ) -> T:
        """The single retry layer of every Gemini call (docs/AI_SYSTEM_SPEC.md, section 4).

        `operation` may change its request between attempts (for example, asking only for
        what is still missing), so a schema error is never repeated with the same input.
        """

        return await call_with_retries(
            operation,
            provider=PROVIDER,
            model=self.model,
            prompt_version=prompt_version,
            max_attempts=self.max_attempts,
        )

    async def generate[T](
        self, contents: list[Any], prompt_version: str, parse: Callable[[str | None], T]
    ) -> T:
        """Generate and parse; a response that fails `parse` is retried like a transient error."""

        async def run() -> T:
            return parse(await self._generate(contents))

        return await self.with_retries(run, prompt_version)

    async def complete_json_once(self, prompt: str) -> dict[str, Any]:
        """One call, no retries: for use inside an operation passed to `with_retries`."""

        return parse_json_object(await self._generate([prompt]))
