"""Ports implemented by infrastructure adapters (docs/architecture/MODULE_STRUCTURE.md)."""

from dataclasses import dataclass
from datetime import datetime, timedelta
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

    async def delete_prefix(self, prefix: str) -> None:
        """Remove every object whose key starts with `prefix` (missing ones are ignored)."""
        ...


class PolicyRepository(Protocol):
    async def save(self, policy: Policy) -> None: ...

    async def get(self, policy_id: str) -> Policy | None:
        """Return None for unknown ids and for legacy records without an owner."""
        ...

    async def list_recent(self, owner_id: str, limit: int) -> list[Policy]:
        """The owner's policies, newest first (expired ones included)."""
        ...

    async def delete(self, policy_id: str) -> None: ...

    async def delete_all_for_owner(self, owner_id: str) -> None: ...

    async def list_expired(self, before: datetime, limit: int) -> list[Policy]: ...


class ComparisonRepository(Protocol):
    async def save(self, comparison: Comparison) -> None: ...

    async def get(self, comparison_id: str) -> Comparison | None:
        """Return None for unknown ids and for legacy records without an owner."""
        ...

    async def list_recent(self, owner_id: str, limit: int) -> list[Comparison]:
        """The owner's comparisons, newest first (expired ones included)."""
        ...

    async def count_active(self, owner_id: str, now: datetime) -> int:
        """How many of the owner's comparisons are not expired at `now`."""
        ...

    async def delete(self, comparison_id: str) -> None: ...

    async def delete_all_for_owner(self, owner_id: str) -> None: ...

    async def list_expired(self, before: datetime, limit: int) -> list[Comparison]: ...


@dataclass(frozen=True, slots=True)
class Identity:
    """An authenticated caller. `uid` is the anonymous account id (the data owner)."""

    uid: str


class IdentityVerifier(Protocol):
    async def verify(self, token: str, check_revoked: bool = False) -> Identity:
        """Validate a bearer token.

        Raise `AuthenticationError` (401) with AUTH_TOKEN_EXPIRED, AUTH_TOKEN_INVALID or
        AUTH_TOKEN_REVOKED, or `InfrastructureError` AUTH_UNAVAILABLE (503) when the
        identity provider cannot be reached.
        """
        ...


class AccountRemover(Protocol):
    async def remove(self, uid: str) -> None:
        """Delete the anonymous account; a missing account is not an error."""
        ...


class RateLimiter(Protocol):
    def allow(self, key: str, limit: int, window: timedelta) -> bool:
        """Record one hit for `key` and tell whether it is within `limit` per `window`."""
        ...


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
    encrypted: bool = False
    unreadable: bool = False

    @property
    def searchable(self) -> bool:
        """At least half of the pages carry a real text layer."""

        if not self.page_count:
            return False
        with_text = sum(1 for text in self.page_texts.values() if len(text) >= MIN_CHARS_PER_PAGE)
        return with_text / self.page_count >= 0.5


class PdfTextReader(Protocol):
    def read(self, data: bytes) -> PdfText: ...


class DocumentUnreadableError(Exception):
    """The file's content cannot be parsed (corrupted or malformed)."""


@dataclass(frozen=True, slots=True)
class DocxText:
    """Text of a DOCX in document order, grouped into stable logical pages.

    DOCX has no fixed pagination, so a logical page starts at an explicit page
    break, at a section break or when a block reaches its size cap. The numbers
    are deterministic for the same file and are 1-based like PDF pages.
    """

    page_texts: dict[int, str]

    @property
    def page_count(self) -> int:
        return len(self.page_texts)

    @property
    def has_text(self) -> bool:
        return any(text.strip() for text in self.page_texts.values())


class DocxTextReader(Protocol):
    def read(self, data: bytes) -> DocxText:
        """Raise `DocumentUnreadableError` when the file cannot be parsed."""
        ...


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
