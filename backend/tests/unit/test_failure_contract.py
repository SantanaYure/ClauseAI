"""Failure code/retryable exposure, DOCX wording in the quality gate and storage failures."""

from pathlib import Path

import pytest
from app.application.use_cases import PolicyService, UploadLimits
from app.domain.interfaces.ports import DocumentContent, StoredObject
from app.domain.services.scoring import ScoringParameters, build_quality_gate
from app.domain.value_objects import DocumentStatus, FileKind
from app.infrastructure.events import InMemoryEventBus
from app.infrastructure.knowledge_base import JsonConceptCatalog
from app.infrastructure.persistence import InMemoryPolicyRepository
from app.infrastructure.word import PythonDocxTextReader
from app.presentation.api.schemas.domain import PolicyDocumentResponse
from app.shared.exceptions import ApplicationError, InfrastructureError
from fastapi.testclient import TestClient

from tests.fakes import PDF_BYTES, FakeExtractor, FakePdfReader, build_test_app, make_docx
from tests.integration.test_api_flow import wait_for
from tests.unit.test_ai_resilience import _ready_policy
from tests.unit.test_docx_support import _command, _service

KB = JsonConceptCatalog().load()


class _FailingExtractor(FakeExtractor):
    def __init__(self, error: Exception) -> None:
        super().__init__()
        self._error = error

    async def extract(self, content: DocumentContent, kb):  # type: ignore[no-untyped-def]
        raise self._error


def _provider(code: str, retryable: bool) -> InfrastructureError:
    return InfrastructureError("x", code=code, details={"retryable": retryable})


@pytest.mark.parametrize(
    ("error", "code", "retryable"),
    [
        (
            InfrastructureError("x", code="MODEL_UNAVAILABLE", details={"retryable": True}),
            "MODEL_UNAVAILABLE",
            True,
        ),
        (
            InfrastructureError("x", code="AI_AUTH_FAILED", details={"retryable": False}),
            "AI_AUTH_FAILED",
            False,
        ),
        (RuntimeError("boom"), "UNEXPECTED_ERROR", True),
    ],
)
async def test_worker_failure_persists_code_and_retryable(
    tmp_path: Path, error: Exception, code: str, retryable: bool
) -> None:
    service = _service(tmp_path, _FailingExtractor(error))  # type: ignore[arg-type]
    policy = await service.create_policy(_command(("a.docx", make_docx())))

    await service.process_policy(policy.id)

    document = (await service.get_policy(policy.id)).documents[0]
    assert document.status == DocumentStatus.FAILED
    assert (document.failure_code, document.failure_retryable) == (code, retryable)
    body = PolicyDocumentResponse.of(document).model_dump()
    assert body["failure_code"] == code and body["failure_retryable"] is retryable
    assert body["failure"]  # the existing field is untouched


def test_api_exposes_failure_fields_additively(tmp_path: Path) -> None:
    app = build_test_app(tmp_path, _FailingExtractor(ApplicationError("Falhou.", code="X_CODE")))
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/policies",
            data={"document_types": ["POLICY"]},
            files=[("files", ("a.pdf", PDF_BYTES, "application/pdf"))],
        )
        detail = wait_for(
            client,
            f"/api/v1/policies/{created.json()['policy_id']}",
            {"FAILED", "READY", "ATTENTION"},
        )
    document = detail["documents"][0]
    assert document["failure"] == "Falhou."
    assert document["failure_code"] == "X_CODE"
    assert document["failure_retryable"] is False


async def test_quality_gate_says_blocks_for_docx() -> None:
    from app.domain.services.scoring import build_items, build_pairs, build_profiles, build_summary
    from app.infrastructure.persistence import InMemoryPolicyRepository as Repo

    repo = Repo()
    await _ready_policy(repo, "a")
    await _ready_policy(repo, "b")
    a, b = await repo.get("a"), await repo.get("b")
    assert a and b
    for policy in (a, b):
        policy.documents[0].file_kind = FileKind.DOCX
        policy.documents[0].pages = 4
    params = ScoringParameters()
    items = build_items(build_pairs(KB, a, b), {}, params)
    base = build_profiles(items, params)[0]
    gate = build_quality_gate(a, b, items, build_summary(items, base, params), KB, params)
    checks = {c.id: c for c in gate}

    assert "blocos" in checks["pages"].label and checks["pages"].detail == "8 blocos (DOCX)."
    assert "bloco" in checks["references"].label

    a.documents[0].file_kind = FileKind.SEARCHABLE_PDF
    mixed = {
        c.id: c
        for c in build_quality_gate(a, b, items, build_summary(items, base, params), KB, params)
    }
    assert mixed["pages"].detail == "4 páginas e 4 blocos (DOCX)."


class _BrokenStorage:
    def __init__(self, fail_on: int) -> None:
        self.fail_on, self.puts, self.deleted = fail_on, [], []

    async def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        if len(self.puts) + 1 == self.fail_on:
            raise OSError("disco cheio")
        self.puts.append(key)
        return StoredObject(key, len(data), "sum")

    async def get(self, key: str) -> bytes:
        return b""

    async def delete(self, key: str) -> None:
        self.deleted.append(key)


async def test_storage_failure_maps_to_503_without_creating_a_policy() -> None:
    storage = _BrokenStorage(fail_on=2)
    repository = InMemoryPolicyRepository()
    service = PolicyService(
        repository=repository,
        storage=storage,  # type: ignore[arg-type]
        catalog=JsonConceptCatalog(),
        extractor=FakeExtractor(),
        pdf_reader=FakePdfReader(),
        docx_reader=PythonDocxTextReader(),
        event_bus=InMemoryEventBus(),
        limits=UploadLimits(max_file_bytes=1024 * 1024, max_files=5, min_evidence_confidence=0.7),
    )

    with pytest.raises(ApplicationError) as error:
        await service.create_policy(_command(("a.docx", make_docx()), ("b.docx", make_docx())))

    assert error.value.code == "STORAGE_UNAVAILABLE"
    assert error.value.status_code == 503
    assert storage.deleted == storage.puts  # first original is not left orphaned
    assert await repository.list_recent(10) == []
