"""Deterministic guardrails applied to AI output before it becomes domain data.

They enforce the inviolable rules of docs/domain/DO_KNOWLEDGE_BASE.md (section 3)
regardless of what a model returns.
"""

from app.domain.entities import AssessmentDecision, ConceptOccurrence, Evidence
from app.domain.services.text import normalize_text
from app.domain.value_objects import (
    CONTRACTUAL_DOCUMENT_TYPES,
    ContractStatus,
    DocumentType,
    Level,
)

BASE_RESULT_SCALE = (0.0, 0.25, 0.5, 0.75, 1.0)
ADJUSTMENT_FACTOR_SCALE = (0.0, 0.25, 0.5, 0.75, 0.9, 1.0)

# Highest Resultado-base allowed for each contract status (knowledge base, 6.2).
_BASE_CAP = {
    ContractStatus.CONTRACTED: 1.0,
    ContractStatus.DIVERGENT: 0.5,
    ContractStatus.NOT_PROVEN: 0.25,
    ContractStatus.NOT_FOUND: 0.0,
    ContractStatus.EXCLUDED: 0.0,
}

MISSING_JUSTIFICATION = "Redução aplicada sem justificativa do modelo; revisar a evidência."


def snap(value: float, scale: tuple[float, ...]) -> float:
    """Round a model value to the nearest allowed scale step."""

    return min(scale, key=lambda step: abs(step - value))


def enforce_contract_rule(
    occurrence: ConceptOccurrence, document_type: DocumentType
) -> ConceptOccurrence:
    """General conditions or proposals never prove contracting (rule 3)."""

    if (
        occurrence.contract_status == ContractStatus.CONTRACTED
        and document_type not in CONTRACTUAL_DOCUMENT_TYPES
    ):
        note = (
            "Previsto no documento, sem comprovação contratual (apólice, especificação ou endosso)."
        )
        return occurrence.model_copy(
            update={
                "contract_status": ContractStatus.NOT_PROVEN,
                "justification": note,
                "confidence": Level.MEDIUM,
            }
        )
    return occurrence


def enforce_evidence_rule(occurrence: ConceptOccurrence) -> ConceptOccurrence:
    """Without a literal excerpt nothing can be contracted or excluded (rules 1 and 6)."""

    if occurrence.evidence or occurrence.contract_status in (
        ContractStatus.NOT_FOUND,
        ContractStatus.NOT_PROVEN,
    ):
        return occurrence
    return occurrence.model_copy(
        update={
            "contract_status": ContractStatus.NOT_PROVEN,
            "justification": "O modelo não apresentou trecho literal que sustente a classificação.",
            "confidence": Level.LOW,
        }
    )


def verify_evidence(
    evidence: Evidence, page_texts: dict[int, str], min_confidence: float
) -> Evidence:
    """Lower confidence when the quoted text is not found in the native page text."""

    page_text = page_texts.get(evidence.page)
    if not page_text:
        return evidence
    quote = normalize_text(evidence.text)[:80]
    if quote and quote in normalize_text(page_text):
        return evidence
    return evidence.model_copy(
        update={"confidence": min(evidence.confidence, min_confidence - 0.1)}
    )


def sanitize_decision(decision: AssessmentDecision, status: ContractStatus) -> AssessmentDecision:
    """Clamp an AI assessment to the scales and to what the evidence allows."""

    base = min(snap(decision.base_result, BASE_RESULT_SCALE), _BASE_CAP[status])
    factor = snap(decision.adjustment_factor, ADJUSTMENT_FACTOR_SCALE)
    confidence = decision.confidence
    if status in (ContractStatus.EXCLUDED, ContractStatus.NOT_FOUND):
        base, factor = 0.0, 0.0
    justification = (decision.justification or "").strip() or None
    if (base < 1.0 or factor < 1.0) and not justification:
        if status == ContractStatus.EXCLUDED:
            justification = "Exclusão expressa."
        elif status == ContractStatus.NOT_FOUND:
            justification = "Não localizado nos documentos enviados."
        else:
            justification = MISSING_JUSTIFICATION
            confidence = Level.LOW
    return AssessmentDecision(
        base_result=base,
        adjustment_factor=factor,
        justification=justification,
        confidence=confidence,
    )
