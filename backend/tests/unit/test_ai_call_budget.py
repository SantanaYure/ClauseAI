"""Single retry layer on the Gemini calls (docs/AI_SYSTEM_SPEC.md, section 4), without Gemini."""

import json
from types import SimpleNamespace
from typing import Any

import pytest
from app.domain.entities import ExecutiveSummary
from app.domain.interfaces.ports import AssessmentRequest
from app.domain.value_objects import DecisionMode
from app.infrastructure.ai import support
from app.infrastructure.ai.assessment import GeminiConceptAssessor, GeminiSummaryWriter
from app.infrastructure.ai.gemini_client import GeminiClient
from app.shared.exceptions import InfrastructureError

MAX_ATTEMPTS = 3


@pytest.fixture(autouse=True)
def no_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    async def instant(_: float) -> None:
        return None

    monkeypatch.setattr(support.asyncio, "sleep", instant)


class _ScriptedGemini:
    """Stands in for the SDK: returns the scripted texts and records every prompt."""

    def __init__(self, answers: list[str]) -> None:
        self._answers = answers
        self.prompts: list[str] = []

    async def generate_content(self, *, contents: list[Any], **_: Any) -> Any:
        self.prompts.append(contents[0])
        return SimpleNamespace(text=self._answers[len(self.prompts) - 1], candidates=[])


def _client(answers: list[str]) -> tuple[GeminiClient, _ScriptedGemini]:
    client = GeminiClient(api_key="x", model="m", timeout_seconds=1, max_attempts=MAX_ATTEMPTS)
    fake = _ScriptedGemini(answers)
    client._client = SimpleNamespace(aio=SimpleNamespace(models=fake))  # type: ignore[assignment]
    return client, fake


def _request(concept_id: str) -> AssessmentRequest:
    return AssessmentRequest(
        concept_id=concept_id,
        concept_name=f"Conceito {concept_id}",
        criterion="critério",
        weight=5,
        policy_a={"contract_status": "CONTRACTED"},
        policy_b={"contract_status": "NOT_FOUND"},
    )


def _answer(*concept_ids: str) -> str:
    decision = {"base_result": 1.0, "adjustment_factor": 1.0}
    return json.dumps(
        {"assessments": [{"concept_id": c, "a": decision, "b": decision} for c in concept_ids]}
    )


def _asked(prompt: str, concept_id: str) -> bool:
    return f'"concept_id":"{concept_id}"' in prompt


async def test_happy_path_makes_a_single_call() -> None:
    client, fake = _client([_answer("DO-001", "DO-002")])

    result = await GeminiConceptAssessor(client).assess([_request("DO-001"), _request("DO-002")])

    assert [r.concept_id for r in result] == ["DO-001", "DO-002"]
    assert len(fake.prompts) == 1


async def test_retry_asks_only_for_the_missing_concepts_and_merges() -> None:
    client, fake = _client([_answer("DO-001"), _answer("DO-002")])

    result = await GeminiConceptAssessor(client).assess([_request("DO-001"), _request("DO-002")])

    assert [r.concept_id for r in result] == ["DO-001", "DO-002"]
    assert len(fake.prompts) == 2
    retry = fake.prompts[1]
    assert _asked(retry, "DO-002") and not _asked(retry, "DO-001")


async def test_schema_errors_stop_at_max_attempts_in_total() -> None:
    client, fake = _client(["não é json"] * 10)

    with pytest.raises(InfrastructureError) as raised:
        await GeminiConceptAssessor(client).assess([_request("DO-001")])

    assert raised.value.code == "INVALID_MODEL_OUTPUT"
    assert len(fake.prompts) == MAX_ATTEMPTS


async def test_concepts_never_answered_stop_at_max_attempts_in_total() -> None:
    client, fake = _client([_answer("DO-001")] * 10)

    with pytest.raises(InfrastructureError):
        await GeminiConceptAssessor(client).assess([_request("DO-001"), _request("DO-002")])

    assert len(fake.prompts) == MAX_ATTEMPTS
    assert all(not _asked(p, "DO-001") for p in fake.prompts[1:])


async def test_invalid_item_is_dropped_and_asked_again() -> None:
    broken = json.dumps({"assessments": [{"concept_id": "DO-001", "a": "?", "b": "?"}]})
    client, fake = _client([broken, _answer("DO-001")])

    result = await GeminiConceptAssessor(client).assess([_request("DO-001")])

    assert [r.concept_id for r in result] == ["DO-001"]
    assert len(fake.prompts) == 2


def _summary(conclusion: str) -> ExecutiveSummary:
    return ExecutiveSummary(
        decision_mode=DecisionMode.CONDITIONED,
        highest_score="A",
        advantages_a=[],
        advantages_b=[],
        equivalent_critical=[],
        highest_impact=[],
        attention_points=[],
        score_vs_qualitative=None,
        conclusion=conclusion,
    )


async def test_summary_writer_keeps_deterministic_text_when_the_guard_rejects() -> None:
    deterministic = "A Apólice 01 tem o maior score de aderência (80,0%), mas é condicionado."
    client, fake = _client([json.dumps({"conclusion": "A Apólice 01 é a vencedora."})])

    text = await GeminiSummaryWriter(client).write_conclusion(
        _summary(deterministic), {"conclusao_deterministica": deterministic}
    )

    assert text == deterministic
    assert len(fake.prompts) == 1


async def test_summary_writer_retries_a_bad_schema_within_the_same_budget() -> None:
    accepted = "A Apólice 01 lidera com 80,0%, mas as duas seguem como alternativas."
    client, fake = _client(['{"texto": "x"}', json.dumps({"conclusion": accepted})])

    text = await GeminiSummaryWriter(client).write_conclusion(
        _summary("determinístico"), {"score_aderencia_apolice_01": "80,0%"}
    )

    assert text == accepted
    assert len(fake.prompts) == 2
