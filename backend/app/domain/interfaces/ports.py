"""Ports implemented by infrastructure adapters (docs/architecture/MODULE_STRUCTURE.md)."""

from dataclasses import dataclass
from typing import Protocol

from app.domain.entities import (
    Comparison,
    ConceptAssessment,
    ExecutiveSummary,
    ExtractionResult,
    KnowledgeBase,
    Policy,
    PolicyDocument,
)


@dataclass(frozen=True, slots=True)
class StoredObject:
    storage_key: str
    size_bytes: int
    checksum_sha256: str


class BlobStorage(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> StoredObject: ...

    async def get(self, key: str) -> bytes: ...

    async def delete(self, key: str) -> None:
        """Remove the object; deleting a missing key is not an error."""
        ...


class PolicyRepository(Protocol):
    async def save(self, policy: Policy) -> None: ...

    async def get(self, policy_id: str) -> Policy | None: ...

    async def list_recent(self, limit: int) -> list[Policy]: ...

    async def delete(self, policy_id: str) -> None: ...


class ComparisonRepository(Protocol):
    async def save(self, comparison: Comparison) -> None: ...

    async def get(self, comparison_id: str) -> Comparison | None: ...

    async def list_recent(self, limit: int) -> list[Comparison]: ...


class ConceptCatalog(Protocol):
    def load(self) -> KnowledgeBase: ...


@dataclass(frozen=True, slots=True)
class DocumentContent:
    """Everything the extractor needs about one document."""

    document: PolicyDocument
    data: bytes
    page_texts: dict[int, str]


MIN_CHARS_PER_PAGE = 40


@dataclass(frozen=True, slots=True)
class PdfText:
    page_count: int
    page_texts: dict[int, str]

    @property
    def searchable(self) -> bool:
        """At least half of the pages carry a real text layer."""

        if not self.page_count:
            return False
        with_text = sum(1 for text in self.page_texts.values() if len(text) >= MIN_CHARS_PER_PAGE)
        return with_text / self.page_count >= 0.5


class PdfTextReader(Protocol):
    def read(self, data: bytes) -> PdfText: ...


class PolicyExtractor(Protocol):
    """P-EXTRACT-001 / P-NORMALIZE-001 (Gemini)."""

    async def extract(
        self, content: DocumentContent, knowledge_base: KnowledgeBase
    ) -> ExtractionResult: ...


@dataclass(frozen=True, slots=True)
class AssessmentRequest:
    """One concept to assess, already reduced to the evidence both policies hold."""

    concept_id: str
    concept_name: str
    criterion: str
    weight: int
    policy_a: dict[str, object]
    policy_b: dict[str, object]


class ConceptAssessor(Protocol):
    """P-ASSESS-001 (Gemini)."""

    async def assess(self, requests: list[AssessmentRequest]) -> list[ConceptAssessment]: ...

    @property
    def model_name(self) -> str: ...


class SummaryWriter(Protocol):
    """P-EXECUTIVE-001 (Gemini): rewrites only the conclusion text."""

    async def write_conclusion(
        self, summary: ExecutiveSummary, facts: dict[str, object]
    ) -> str: ...
