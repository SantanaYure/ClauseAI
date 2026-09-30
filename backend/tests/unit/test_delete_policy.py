from pathlib import Path

import pytest
from app.application.use_cases import PolicyService, UploadLimits
from app.domain.entities import Policy, utc_now
from app.domain.value_objects import PolicyStatus
from app.infrastructure.events import InMemoryEventBus
from app.infrastructure.knowledge_base import JsonConceptCatalog
from app.infrastructure.persistence import InMemoryPolicyRepository
from app.infrastructure.storage import LocalBlobStorage
from app.infrastructure.word import PythonDocxTextReader
from app.shared.exceptions import ApplicationError

from tests.fakes import OWNER, RETENTION, FakeExtractor, FakePdfReader, make_quotas


async def test_policy_being_processed_cannot_be_deleted(tmp_path: Path) -> None:
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
    await repository.save(
        Policy(
            owner_id=OWNER,
            expires_at=utc_now() + RETENTION,
            id="pol_1",
            insurer="X",
            name="Y",
            status=PolicyStatus.PROCESSING,
            correlation_id="c",
        )
    )

    with pytest.raises(ApplicationError) as error:
        await service.delete_policy(OWNER, "pol_1")

    assert error.value.code == "POLICY_PROCESSING"
    assert error.value.status_code == 409
    assert await repository.get("pol_1") is not None
