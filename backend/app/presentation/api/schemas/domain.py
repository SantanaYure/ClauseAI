"""HTTP DTOs for the /api/v1 contracts (docs/architecture/PERSISTENCE_AND_API.md).

`owner_id` is never exposed; `expires_at` (UTC) tells when the item will be deleted.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities import (
    Comparison,
    ComparisonItem,
    Concept,
    ConceptOccurrence,
    ExecutiveSummary,
    Failure,
    Policy,
    PolicyDocument,
    PolicyRef,
    ProfileResult,
    QualityCheck,
)
from app.domain.value_objects import (
    ComparisonStatus,
    DecisionMode,
    DocumentStatus,
    DocumentType,
    FileKind,
    Level,
    PolicyStatus,
    RiskProfile,
)


class Dto(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Page[T](Dto):
    items: list[T]
    next_cursor: str | None = None


class PolicyDocumentResponse(Dto):
    id: str
    filename: str
    type: DocumentType
    file_kind: FileKind
    pages: int
    status: DocumentStatus
    extraction_quality: Level | None
    ocr_required: bool
    failure: str | None
    failure_code: str | None = None
    failure_retryable: bool = False

    @classmethod
    def of(cls, document: PolicyDocument) -> "PolicyDocumentResponse":
        return cls(
            id=document.id,
            filename=document.filename,
            type=document.type,
            file_kind=document.file_kind,
            pages=document.pages,
            status=document.status,
            extraction_quality=document.extraction_quality,
            ocr_required=document.ocr_required,
            failure=document.failure,
            failure_code=document.failure_code,
            failure_retryable=document.failure_retryable,
        )


class PolicySummaryResponse(Dto):
    id: str
    insurer: str
    name: str
    number: str | None
    validity: str | None
    status: PolicyStatus
    documents: list[PolicyDocumentResponse]
    alerts: list[str]
    expires_at: datetime

    @classmethod
    def of(cls, policy: Policy) -> "PolicySummaryResponse":
        return cls(
            id=policy.id,
            insurer=policy.insurer,
            name=policy.name,
            number=policy.number,
            validity=policy.validity,
            status=policy.status,
            expires_at=policy.expires_at,
            documents=[PolicyDocumentResponse.of(d) for d in policy.documents],
            alerts=policy.alerts,
        )


class PolicyDetailResponse(PolicySummaryResponse):
    occurrences: list[ConceptOccurrence]
    knowledge_base_version: str | None

    @classmethod
    def of(cls, policy: Policy) -> "PolicyDetailResponse":
        summary = PolicySummaryResponse.of(policy).model_dump()
        return cls(
            **summary,
            occurrences=policy.occurrences,
            knowledge_base_version=policy.knowledge_base_version,
        )


class PolicyCreatedResponse(Dto):
    policy_id: str
    status: PolicyStatus
    document_ids: list[str]
    expires_at: datetime
    correlation_id: str


class ComparisonCreateRequest(Dto):
    policy_a_id: str = Field(min_length=1)
    policy_b_id: str = Field(min_length=1)
    selected_profile: RiskProfile = RiskProfile.BASE


class ComparisonCreatedResponse(Dto):
    comparison_id: str
    status: ComparisonStatus
    expires_at: datetime
    correlation_id: str


class ComparisonResponse(Dto):
    """Full comparison result, without the owner."""

    id: str
    created_at: datetime
    completed_at: datetime | None
    expires_at: datetime
    status: ComparisonStatus
    knowledge_base_version: str
    selected_profile: RiskProfile
    policy_a: PolicyRef
    policy_b: PolicyRef
    items: list[ComparisonItem]
    profiles: list[ProfileResult]
    summary: ExecutiveSummary | None
    quality_gate: list[QualityCheck]
    failure: Failure | None
    correlation_id: str
    models: dict[str, str]

    @classmethod
    def of(cls, comparison: Comparison) -> "ComparisonResponse":
        return cls.model_validate(comparison.model_dump(exclude={"owner_id"}))


class ComparisonListItemResponse(Dto):
    id: str
    created_at: datetime
    expires_at: datetime
    status: ComparisonStatus
    policy_a: PolicyRef
    policy_b: PolicyRef
    adherence_a: float | None
    adherence_b: float | None
    decision_mode: DecisionMode | None
    failure_reason: str | None
    failure_code: str | None = None
    failure_retryable: bool = False

    @classmethod
    def of(cls, comparison: Comparison) -> "ComparisonListItemResponse":
        base = next((p for p in comparison.profiles if p.profile == RiskProfile.BASE), None)
        return cls(
            id=comparison.id,
            created_at=comparison.created_at,
            expires_at=comparison.expires_at,
            status=comparison.status,
            policy_a=comparison.policy_a,
            policy_b=comparison.policy_b,
            adherence_a=base.a.adherence if base else None,
            adherence_b=base.b.adherence if base else None,
            decision_mode=comparison.summary.decision_mode if comparison.summary else None,
            failure_reason=comparison.failure.message if comparison.failure else None,
            failure_code=comparison.failure.code if comparison.failure else None,
            failure_retryable=comparison.failure.retryable if comparison.failure else False,
        )


class OccurrenceMatchResponse(Dto):
    policy: PolicyRef
    occurrence: ConceptOccurrence | None


class QueryRequest(Dto):
    question: str = Field(min_length=2, max_length=500)


class QueryAnswerResponse(Dto):
    question: str
    concept: Concept | None
    answer: str
    matches: list[OccurrenceMatchResponse]
    guidance: bool


class OwnerDataSummaryResponse(Dto):
    """What "delete all my data" will erase."""

    policies: int
    documents: int
    comparisons: int
