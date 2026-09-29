"""Concept assessment and executive conclusion on Gemini
(P-ASSESS-001, P-EXECUTIVE-001, ADR-018, ADR-023)."""

import json
import re

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.domain.entities import AssessmentDecision, ConceptAssessment, ExecutiveSummary
from app.domain.interfaces.ports import AssessmentRequest
from app.infrastructure.ai.gemini_client import GeminiClient
from app.infrastructure.ai.support import InvalidModelOutput, load_prompt, render

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


class GeminiSummaryWriter:
    def __init__(self, client: GeminiClient) -> None:
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
