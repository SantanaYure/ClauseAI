"""Groq adapter (GPT-OSS): concept assessment and executive conclusion
(P-ASSESS-001, P-EXECUTIVE-001, ADR-007, ADR-018)."""

import json
import re
from typing import Literal

from groq import (
    APIConnectionError,
    APITimeoutError,
    AsyncGroq,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.domain.entities import AssessmentDecision, ConceptAssessment, ExecutiveSummary
from app.domain.interfaces.ports import AssessmentRequest
from app.infrastructure.ai.support import (
    InvalidModelOutput,
    RateLimitedError,
    TransientProviderError,
    call_with_retries,
    load_prompt,
    parse_json_object,
    render,
    retry_after_seconds,
)

ASSESS_PROMPT = "P-ASSESS-001"
EXECUTIVE_PROMPT = "P-EXECUTIVE-001"


class _AssessmentOut(BaseModel):
    concept_id: str
    a: AssessmentDecision
    b: AssessmentDecision
    main_difference: str = ""


class _AssessmentsOut(BaseModel):
    assessments: list[_AssessmentOut]


class _ConclusionOut(BaseModel):
    conclusion: str


class GroqClient:
    """One Groq client shared by the assessor and the summary writer."""

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_attempts: int,
        batch_size: int = 6,
        reasoning_effort: Literal["low", "medium", "high"] = "low",
    ) -> None:
        self._client = AsyncGroq(api_key=api_key, timeout=timeout_seconds, max_retries=0)
        self.model = model
        self.max_attempts = max_attempts
        self.batch_size = batch_size
        self._reasoning_effort = reasoning_effort
        self._system = load_prompt("P-SYSTEM-001")

    async def complete_json(self, prompt: str, prompt_version: str) -> dict[str, object]:
        async def run() -> dict[str, object]:
            try:
                response = await self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0,
                    response_format={"type": "json_object"},
                    reasoning_effort=self._reasoning_effort,
                )
            except RateLimitError as exc:
                headers = getattr(exc.response, "headers", None)
                raise RateLimitedError(str(exc), retry_after_seconds(headers, str(exc))) from exc
            except (APITimeoutError, APIConnectionError, InternalServerError) as exc:
                raise TransientProviderError(str(exc)) from exc
            return parse_json_object(response.choices[0].message.content)

        return await call_with_retries(
            run,
            provider="groq",
            model=self.model,
            prompt_version=prompt_version,
            max_attempts=self.max_attempts,
        )


class GroqConceptAssessor:
    def __init__(self, client: GroqClient) -> None:
        self._client = client
        self._template = load_prompt(ASSESS_PROMPT)

    @property
    def model_name(self) -> str:
        return self._client.model

    async def assess(self, requests: list[AssessmentRequest]) -> list[ConceptAssessment]:
        results: list[ConceptAssessment] = []
        size = self._client.batch_size
        for start in range(0, len(requests), size):
            results.extend(await self._assess_batch(requests[start : start + size]))
        return results

    async def _assess_batch(self, batch: list[AssessmentRequest]) -> list[ConceptAssessment]:
        payload = [
            {
                "concept_id": request.concept_id,
                "concept": request.concept_name,
                "criterion": request.criterion,
                "weight": request.weight,
                "a": request.policy_a,
                "b": request.policy_b,
            }
            for request in batch
        ]
        compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        prompt = render(self._template, concepts=compact)
        expected = {request.concept_id for request in batch}

        for _ in range(self._client.max_attempts):
            data = await self._client.complete_json(prompt, ASSESS_PROMPT)
            try:
                parsed = _AssessmentsOut.model_validate(data)
            except PydanticValidationError:
                continue
            by_id = {
                item.concept_id: item for item in parsed.assessments if item.concept_id in expected
            }
            if set(by_id) == expected:
                return [
                    ConceptAssessment(
                        concept_id=item.concept_id,
                        a=item.a,
                        b=item.b,
                        main_difference=item.main_difference,
                    )
                    for item in by_id.values()
                ]
        raise InvalidModelOutput("O modelo não avaliou todos os conceitos solicitados.")


_PERCENT = re.compile(r"\d+(?:[.,]\d+)?\s?%")


class GroqSummaryWriter:
    def __init__(self, client: GroqClient) -> None:
        self._client = client
        self._template = load_prompt(EXECUTIVE_PROMPT)

    async def write_conclusion(self, summary: ExecutiveSummary, facts: dict[str, object]) -> str:
        compact = json.dumps(facts, ensure_ascii=False, separators=(",", ":"))
        prompt = render(self._template, facts=compact)
        data = await self._client.complete_json(prompt, EXECUTIVE_PROMPT)
        try:
            conclusion = _ConclusionOut.model_validate(data).conclusion.strip()
        except PydanticValidationError as exc:
            raise InvalidModelOutput(str(exc)) from exc
        allowed = {
            p.replace(" ", "") for p in _PERCENT.findall(json.dumps(facts, ensure_ascii=False))
        }
        used = {p.replace(" ", "") for p in _PERCENT.findall(conclusion)}
        if not conclusion or not used <= allowed:
            # The model invented or changed a number: keep the deterministic text.
            return summary.conclusion
        return conclusion
