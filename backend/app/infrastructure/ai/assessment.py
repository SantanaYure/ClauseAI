"""Concept assessment and executive conclusion on Gemini
(P-ASSESS-001, P-EXECUTIVE-001, ADR-018, ADR-023)."""

import json
from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.domain.entities import AssessmentDecision, ConceptAssessment, ExecutiveSummary
from app.domain.interfaces.ports import AssessmentRequest
from app.domain.services.conclusion_guard import is_grounded_conclusion
from app.infrastructure.ai.gemini_client import GeminiClient
from app.infrastructure.ai.support import (
    InvalidModelOutput,
    load_prompt,
    parse_json_object,
    render,
)

ASSESS_PROMPT = "P-ASSESS-001"
EXECUTIVE_PROMPT = "P-EXECUTIVE-001"


class _AssessmentOut(BaseModel):
    concept_id: str
    a: AssessmentDecision
    b: AssessmentDecision
    main_difference: str = ""


class _ConclusionOut(BaseModel):
    conclusion: str


class GeminiConceptAssessor:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client
        self._template = load_prompt(ASSESS_PROMPT)

    @property
    def model_name(self) -> str:
        return self._client.model

    async def assess(self, requests: list[AssessmentRequest]) -> list[ConceptAssessment]:
        results: list[ConceptAssessment] = []
        size = self._client.assessment_batch_size
        for start in range(0, len(requests), size):
            results.extend(await self._assess_batch(requests[start : start + size]))
        return results

    async def _assess_batch(self, batch: list[AssessmentRequest]) -> list[ConceptAssessment]:
        """One retry layer: each new attempt asks only for the concepts still missing."""

        collected: dict[str, _AssessmentOut] = {}

        async def attempt() -> list[ConceptAssessment]:
            pending = [request for request in batch if request.concept_id not in collected]
            data = await self._client.complete_json_once(self._prompt(pending))
            collected.update(_valid_assessments(data, {r.concept_id for r in pending}))
            missing = [r.concept_id for r in batch if r.concept_id not in collected]
            if missing:
                raise InvalidModelOutput(
                    "O modelo não avaliou todos os conceitos solicitados: " + ", ".join(missing)
                )
            return [_to_domain(collected[request.concept_id]) for request in batch]

        return await self._client.with_retries(attempt, ASSESS_PROMPT)

    def _prompt(self, requests: list[AssessmentRequest]) -> str:
        payload = [
            {
                "concept_id": request.concept_id,
                "concept": request.concept_name,
                "criterion": request.criterion,
                "weight": request.weight,
                "a": request.policy_a,
                "b": request.policy_b,
            }
            for request in requests
        ]
        compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        return render(self._template, concepts=compact)


def _valid_assessments(data: dict[str, Any], expected: set[str]) -> dict[str, _AssessmentOut]:
    """Assessments that pass the schema, by concept; invalid or unasked items are dropped."""

    items = data.get("assessments")
    if not isinstance(items, list):
        raise InvalidModelOutput("Resposta sem a lista de avaliações.")
    valid: dict[str, _AssessmentOut] = {}
    for item in items:
        try:
            parsed = _AssessmentOut.model_validate(item)
        except PydanticValidationError:
            continue
        if parsed.concept_id in expected:
            valid[parsed.concept_id] = parsed
    return valid


def _to_domain(item: _AssessmentOut) -> ConceptAssessment:
    return ConceptAssessment(
        concept_id=item.concept_id, a=item.a, b=item.b, main_difference=item.main_difference
    )


def _parse_conclusion(text: str | None) -> str:
    try:
        return _ConclusionOut.model_validate(parse_json_object(text)).conclusion.strip()
    except PydanticValidationError as exc:
        raise InvalidModelOutput(str(exc)) from exc


class GeminiSummaryWriter:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client
        self._template = load_prompt(EXECUTIVE_PROMPT)

    async def write_conclusion(self, summary: ExecutiveSummary, facts: dict[str, object]) -> str:
        compact = json.dumps(facts, ensure_ascii=False, separators=(",", ":"))
        prompt = render(self._template, facts=compact)
        conclusion = await self._client.generate([prompt], EXECUTIVE_PROMPT, _parse_conclusion)
        if not is_grounded_conclusion(conclusion, compact, summary.decision_mode):
            # The model invented a number or a winner: keep the deterministic text.
            return summary.conclusion
        return conclusion
