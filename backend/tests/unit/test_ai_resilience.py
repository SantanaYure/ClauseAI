"""Provider error classification, ranged extraction, local provider and degraded comparison."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from app.application.commands import CreateComparisonCommand
from app.application.use_cases import ComparisonService
from app.domain.entities import KnowledgeBase, Policy, PolicyDocument, utc_now
from app.domain.interfaces.ports import AssessmentRequest, DocumentContent
from app.domain.services.scoring import ScoringParameters
from app.domain.value_objects import (
    ComparisonStatus,
    DocumentStatus,
    DocumentType,
    FileKind,
    PolicyStatus,
    RiskProfile,
)
from app.infrastructure.ai.gemini_client import GeminiClient
from app.infrastructure.ai.local import LocalPolicyExtractor
from app.infrastructure.events import InMemoryEventBus
from app.infrastructure.knowledge_base import JsonConceptCatalog
from app.infrastructure.persistence import InMemoryComparisonRepository, InMemoryPolicyRepository
from app.main import build_application
from app.shared.config.settings import Settings
from app.shared.exceptions import InfrastructureError
from google.genai import errors as genai_errors
from google.genai import types

from tests.fakes import (
    OWNER,
    RETENTION,
    FakeExtractor,
    FakeSummaryWriter,
    RecordingExtractor,
    make_docx,
    make_quotas,
)
from tests.unit.test_docx_support import _command, _service

KB = JsonConceptCatalog().load()


# ---------- (A) provider errors ----------


def _client_raising(error: Exception) -> GeminiClient:
    client = GeminiClient(api_key="x", model="m", timeout_seconds=1, max_attempts=1)

    async def boom(**_: Any) -> None:
        raise error

    client._client = SimpleNamespace(  # type: ignore[assignment]
        aio=SimpleNamespace(models=SimpleNamespace(generate_content=boom))
    )
    return client


@pytest.mark.parametrize(
    ("status", "message", "code"),
    [
        (401, "unauthorized", "AI_AUTH_FAILED"),
        (403, "forbidden", "AI_AUTH_FAILED"),
        (400, "API key not valid. Please pass a valid API key.", "AI_AUTH_FAILED"),
        (400, "Request contains an invalid argument", "AI_BAD_REQUEST"),
        (404, "model not found", "AI_MODEL_NOT_FOUND"),
    ],
)
async def test_provider_client_errors_are_classified_and_sanitized(
    status: int, message: str, code: str
) -> None:
    error = genai_errors.ClientError(status, {"error": {"message": message}}, None)
    client = _client_raising(error)

    with pytest.raises(InfrastructureError) as raised:
        await client.complete_json_once("oi")

    assert raised.value.code == code
    assert raised.value.details == {"retryable": False}
    assert message not in raised.value.message


async def test_truncated_output_is_reported_clearly() -> None:
    client = GeminiClient(api_key="x", model="m", timeout_seconds=1, max_attempts=1)
    response = types.GenerateContentResponse(
        candidates=[types.Candidate(finish_reason=types.FinishReason.MAX_TOKENS)]
    )

    async def truncated(**_: Any) -> types.GenerateContentResponse:
        return response

    client._client = SimpleNamespace(  # type: ignore[assignment]
        aio=SimpleNamespace(models=SimpleNamespace(generate_content=truncated))
    )
    with pytest.raises(InfrastructureError) as raised:
        await client.complete_json_once("oi")
    assert raised.value.code == "AI_OUTPUT_TRUNCATED"


async def test_provider_error_is_propagated_to_the_document(tmp_path: Path) -> None:
    class Failing(FakeExtractor):
        async def extract(self, content: DocumentContent, kb: KnowledgeBase) -> Any:
            raise InfrastructureError("Chave inválida.", code="AI_AUTH_FAILED")

    service = _service(tmp_path, Failing())  # type: ignore[arg-type]
    policy = await service.create_policy(_command(("a.docx", make_docx())))

    await service.process_policy(policy.id)

    document = (await service.get_policy(OWNER, policy.id)).documents[0]
    assert document.status == DocumentStatus.FAILED
    assert document.failure == "Chave inválida."


# ---------- (C) ranged extraction ----------


class _ScriptedClient:
    model = "scripted"

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def generate(self, contents: list[Any], prompt_version: str, parse: Any) -> Any:
        self.calls.append(contents[1])
        index = len(self.calls)
        insurer = '"Aurora"' if index == 2 else "null"
        return parse(
            f'{{"intake": {{"insurer": {insurer}}}, "occurrences": [{{"concept_id": "DO-002",'
            '"term": "t", "occurrence_type": "BASIC_COVERAGE", "term_relation": "EXACT_MATCH",'
            f'"contract_status": "CONTRACTED", "evidence": [{{"page": {index}, "clause": "1",'
            '"text": "trecho"}]}]}'
        )


# ---------- (B) local provider ----------


def test_local_provider_starts_without_any_credentials(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        ai_provider="local",
        auth_backend="fake",
        persistence_backend="memory",
        storage_backend="local",
        local_storage_dir=str(tmp_path),
    )
    assert settings.missing_required() == []
    assert build_application(settings) is not None


def test_defaults_still_require_credentials_and_local_is_refused_in_production() -> None:
    assert "GEMINI_API_KEY" in Settings(_env_file=None).missing_required()
    production = Settings(_env_file=None, ai_provider="local", app_env="production")
    assert any("AI_PROVIDER" in item for item in production.missing_required())


async def test_local_extractor_quotes_native_text_deterministically(tmp_path: Path) -> None:
    service = _service(tmp_path, RecordingExtractor())
    policy = await service.create_policy(_command(("a.docx", make_docx())))
    document = policy.documents[0]
    concept = KB.weighted[0]
    text = f"1.2 Cobertura de {concept.variants[0]} incluída.\nOutra linha."

    result = await LocalPolicyExtractor().extract(DocumentContent(document, b"", {3: text}), KB)

    found = next(o for o in result.occurrences if o.concept_id == concept.id)
    assert found.evidence[0].page == 3 and found.evidence[0].clause == "1.2"
    assert found.evidence[0].text in text.replace("\n", " ") or found.evidence[0].text in text
    again = await LocalPolicyExtractor().extract(DocumentContent(document, b"", {3: text}), KB)
    assert again == result


# ---------- (D) degraded comparison ----------


class _FailingAssessor:
    model_name = "failing"

    async def assess(self, requests: list[AssessmentRequest]) -> Any:
        raise InfrastructureError(
            "IA fora do ar.", code="MODEL_UNAVAILABLE", details={"retryable": True}
        )


async def _ready_policy(repo: InMemoryPolicyRepository, policy_id: str) -> None:
    extractor = FakeExtractor()
    document = PolicyDocument(
        id=f"{policy_id}_doc",
        policy_id=policy_id,
        filename="a.pdf",
        type=DocumentType.POLICY,
        content_type="application/pdf",
        file_kind=FileKind.SEARCHABLE_PDF,
        size_bytes=1,
        checksum_sha256="c",
        storage_key="k",
    )
    result = await extractor.extract(DocumentContent(document, b"", {}), KB)
    await repo.save(
        Policy(
            id=policy_id,
            owner_id=OWNER,
            expires_at=utc_now() + RETENTION,
            insurer="X",
            name="Y",
            documents=[document],
            occurrences=result.occurrences,
            status=PolicyStatus.READY,
            correlation_id="c",
        )
    )


async def test_comparison_degrades_to_partial_when_assessment_fails() -> None:
    policies = InMemoryPolicyRepository()
    await _ready_policy(policies, "pol_a")
    await _ready_policy(policies, "pol_b")
    comparisons = InMemoryComparisonRepository()
    service = ComparisonService(
        comparisons=comparisons,
        policies=policies,
        catalog=JsonConceptCatalog(),
        assessor=_FailingAssessor(),  # type: ignore[arg-type]
        summary_writer=FakeSummaryWriter(),
        event_bus=InMemoryEventBus(),
        parameters=ScoringParameters(),
        quotas=make_quotas(),
    )
    created = await service.create_comparison(
        CreateComparisonCommand(
            owner_id=OWNER,
            policy_a_id="pol_a",
            policy_b_id="pol_b",
            selected_profile=RiskProfile.FINANCIAL,
            correlation_id="c",
        )
    )

    await service.run_comparison(created.id)

    result = await service.get_comparison(OWNER, created.id)
    assert result.status == ComparisonStatus.PARTIAL
    assert result.failure is not None
    assert result.failure.code == "MODEL_UNAVAILABLE" and result.failure.retryable
    assert "Avaliação por IA indisponível" in result.failure.message
    unscored = [i for i in result.items if i.a.contract_status == "CONTRACTED"]
    assert unscored and all(not i.a.sufficient_evidence and i.a.points == 0 for i in unscored)
    assert result.summary is not None
