"""Commands: intentions that change state (ADR-015)."""

from dataclasses import dataclass

from app.domain.value_objects import DocumentType, RiskProfile


@dataclass(frozen=True, slots=True)
class UploadedFile:
    filename: str
    declared_content_type: str | None
    data: bytes
    document_type: DocumentType


@dataclass(frozen=True, slots=True)
class CreatePolicyCommand:
    owner_id: str
    insurer: str | None
    name: str | None
    files: list[UploadedFile]
    correlation_id: str


@dataclass(frozen=True, slots=True)
class CreateComparisonCommand:
    owner_id: str
    policy_a_id: str
    policy_b_id: str
    selected_profile: RiskProfile
    correlation_id: str


__all__ = ["CreateComparisonCommand", "CreatePolicyCommand", "UploadedFile"]
