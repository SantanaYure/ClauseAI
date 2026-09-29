"""Domain entities (docs/architecture/DOMAIN_MODEL.md).

Pydantic is used only as a typed data container; nothing here depends on HTTP,
Firebase or AI SDKs.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects import (
    ComparisonStatus,
    ContractStatus,
    DecisionMode,
    DocumentStatus,
    DocumentType,
    ExtractionMethod,
    FileKind,
    Importance,
    Level,
    LimitBasis,
    OccurrenceType,
    PolicyStatus,
    RiskProfile,
    TermRelation,
    Verdict,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


# ---------- Knowledge base ----------


class Concept(DomainModel):
    id: str
    domain: str
    name: str
    variants: list[str]
    importance: Importance
    weight: int | None
    justification: str | None = None
    criterion: str
    related: list[str] = Field(default_factory=list)
    human_review: str
    pending_validation: bool = False
    model_question: str | None = None
    extraction_rule: str | None = None


class KnowledgeBase(DomainModel):
    version: str
    concepts: list[Concept]

    def get(self, concept_id: str) -> Concept | None:
        return next((concept for concept in self.concepts if concept.id == concept_id), None)

    @property
    def weighted(self) -> list[Concept]:
        return [concept for concept in self.concepts if concept.weight is not None]


# ---------- Policies ----------


class Evidence(DomainModel):
    id: str
    document_id: str
    document_name: str
    page: int
    clause: str
    text: str
    method: ExtractionMethod
    confidence: float


class ConceptOccurrence(DomainModel):
    concept_id: str
    term: str
    occurrence_type: OccurrenceType
    term_relation: TermRelation
    contract_status: ContractStatus
    justification: str | None = None
    evidence: list[Evidence]
    confidence: Level
    alternative_concepts: list[str] = Field(default_factory=list)
    limit_basis: LimitBasis | None = None
    amount: str | None = None


class PolicyDocument(DomainModel):
    id: str
    policy_id: str
    filename: str
    type: DocumentType
    content_type: str
    file_kind: FileKind
    size_bytes: int
    checksum_sha256: str
    storage_key: str
    pages: int = 0
    status: DocumentStatus = DocumentStatus.UPLOADED
    extraction_quality: Level | None = None
    ocr_required: bool = False
    failure: str | None = None
    uploaded_at: datetime = Field(default_factory=utc_now)


class Policy(DomainModel):
    id: str
    insurer: str
    name: str
    number: str | None = None
    validity: str | None = None
    status: PolicyStatus = PolicyStatus.PROCESSING
    documents: list[PolicyDocument] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)
    occurrences: list[ConceptOccurrence] = Field(default_factory=list)
    knowledge_base_version: str | None = None
    correlation_id: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# ---------- Extraction ----------


class DocumentIntake(DomainModel):
    """Document metadata identified by the extractor (prompt 2)."""

    insurer: str | None = None
    policy_name: str | None = None
    policy_number: str | None = None
    validity: str | None = None
    document_type: DocumentType | None = None
    language: str | None = None


class ExtractionResult(DomainModel):
    intake: DocumentIntake
    occurrences: list[ConceptOccurrence]
    model: str
    prompt_version: str


# ---------- Comparisons ----------


class PolicyRef(DomainModel):
    id: str
    insurer: str
    name: str


class ComparisonSide(DomainModel):
    term: str
    contract_status: ContractStatus
    base_result: float
    adjustment_factor: float
    points: float
    justification: str | None = None
    evidence: list[Evidence]
    sufficient_evidence: bool
    amount: str | None = None


class ComparisonItem(DomainModel):
    concept_id: str
    concept_name: str
    importance: Importance
    weight: int
    a: ComparisonSide
    b: ComparisonSide
    main_difference: str
    verdict: Verdict
    confidence: Level
    guidance: bool


class ScoreSummary(DomainModel):
    raw: float
    max: float
    adherence: float
    documentary: float
    completeness: float
    critical_unconfirmed_weight: int
    inconclusive_weight: float
    favorable: int
    equivalent: int
    inconclusive: int


class ProfileResult(DomainModel):
    profile: RiskProfile
    prioritized: list[str]
    multiplier: float
    a: ScoreSummary
    b: ScoreSummary
    winner: str
    decisive_concepts: list[str]
    sensitivity: str
    limitations: list[str]


class ExecutiveSummary(DomainModel):
    decision_mode: DecisionMode
    highest_score: str
    advantages_a: list[str]
    advantages_b: list[str]
    equivalent_critical: list[str]
    highest_impact: list[str]
    attention_points: list[str]
    score_vs_qualitative: str | None
    conclusion: str


class QualityCheck(DomainModel):
    id: str
    label: str
    passed: bool
    detail: str


class Failure(DomainModel):
    code: str
    message: str


class Comparison(DomainModel):
    id: str
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    status: ComparisonStatus = ComparisonStatus.REQUESTED
    knowledge_base_version: str
    selected_profile: RiskProfile
    policy_a: PolicyRef
    policy_b: PolicyRef
    items: list[ComparisonItem] = Field(default_factory=list)
    profiles: list[ProfileResult] = Field(default_factory=list)
    summary: ExecutiveSummary | None = None
    quality_gate: list[QualityCheck] = Field(default_factory=list)
    failure: Failure | None = None
    correlation_id: str
    models: dict[str, str] = Field(default_factory=dict)


class AssessmentDecision(DomainModel):
    """Per-policy decision proposed by the AI for one concept (P-ASSESS-001)."""

    base_result: float
    adjustment_factor: float
    justification: str | None = None
    confidence: Level = Level.MEDIUM


class ConceptAssessment(DomainModel):
    concept_id: str
    a: AssessmentDecision
    b: AssessmentDecision
    main_difference: str
