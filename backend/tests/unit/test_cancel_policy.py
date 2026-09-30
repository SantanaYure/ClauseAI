from pathlib import Path

import pytest
from app.application.use_cases import PolicyService, UploadLimits
from app.domain.entities import Policy, PolicyDocument, utc_now
from app.domain.value_objects import DocumentStatus, DocumentType, FileKind, PolicyStatus
from app.infrastructure.events import InMemoryEventBus
from app.infrastructure.knowledge_base import JsonConceptCatalog
from app.infrastructure.persistence import InMemoryPolicyRepository
from app.infrastructure.storage import LocalBlobStorage
from app.infrastructure.word import PythonDocxTextReader
from app.shared.exceptions import ApplicationError

from tests.fakes import OWNER, RETENTION, FakeExtractor, FakePdfReader, make_quotas


def _make_service(tmp_path: Path) -> tuple[PolicyService, InMemoryPolicyRepository]:
    repository = InMemoryPolicyRepository()
    service = PolicyService(
        repository=repository,
        storage=LocalBlobStorage(tmp_path),
        catalog=JsonConceptCatalog(),
        extractor=FakeExtractor(),
        pdf_reader=FakePdfReader(),
        docx_reader=PythonDocxTextReader(),
        event_bus=InMemoryEventBus(),
        limits=UploadLimits(max_file_bytes=1024, max_files=5, min_evidence_confidence=0.7),
        quotas=make_quotas(),
        retention=RETENTION,
    )
    return service, repository


async def test_canceling_processing_policy_sets_cancelled_status(tmp_path: Path) -> None:
    service, repository = _make_service(tmp_path)
    doc = PolicyDocument(
        id="doc_1",
        policy_id="pol_1",
        filename="test.pdf",
        type=DocumentType.POLICY,
        content_type="application/pdf",
        file_kind=FileKind.SEARCHABLE_PDF,
        size_bytes=100,
        checksum_sha256="abc",
        storage_key="policies/pol_1/doc_1.pdf",
        ocr_required=False,
        status=DocumentStatus.EXTRACTING,
    )
    await repository.save(
        Policy(
            owner_id=OWNER,
            expires_at=utc_now() + RETENTION,
            id="pol_1",
            insurer="X",
            name="Y",
            status=PolicyStatus.PROCESSING,
            documents=[doc],
            correlation_id="c",
        )
    )

    cancelled = await service.cancel_policy(OWNER, "pol_1")

    assert cancelled.status == PolicyStatus.CANCELLED
    assert cancelled.documents[0].status == DocumentStatus.CANCELLED
    assert "Extração cancelada pelo usuário." in cancelled.alerts
    saved = await repository.get("pol_1")
    assert saved is not None
    assert saved.status == PolicyStatus.CANCELLED


async def test_canceling_non_processing_policy_raises_error(tmp_path: Path) -> None:
    service, repository = _make_service(tmp_path)
    await repository.save(
        Policy(
            owner_id=OWNER,
            expires_at=utc_now() + RETENTION,
            id="pol_ready",
            insurer="X",
            name="Y",
            status=PolicyStatus.READY,
            correlation_id="c",
        )
    )

    with pytest.raises(ApplicationError) as exc_info:
        await service.cancel_policy(OWNER, "pol_ready")

    assert exc_info.value.code == "POLICY_NOT_PROCESSING"


async def test_cancelled_policy_can_be_deleted(tmp_path: Path) -> None:
    service, repository = _make_service(tmp_path)
    doc = PolicyDocument(
        id="doc_1",
        policy_id="pol_1",
        filename="test.pdf",
        type=DocumentType.POLICY,
        content_type="application/pdf",
        file_kind=FileKind.SEARCHABLE_PDF,
        size_bytes=100,
        checksum_sha256="abc",
        storage_key="policies/pol_1/doc_1.pdf",
        ocr_required=False,
        status=DocumentStatus.CANCELLED,
    )
    await repository.save(
        Policy(
            owner_id=OWNER,
            expires_at=utc_now() + RETENTION,
            id="pol_1",
            insurer="X",
            name="Y",
            status=PolicyStatus.CANCELLED,
            documents=[doc],
            correlation_id="c",
        )
    )

    await service.delete_policy(OWNER, "pol_1")
    assert await repository.get("pol_1") is None
