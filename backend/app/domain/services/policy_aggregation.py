"""Consolidates per-document extraction into one policy view."""

from collections import defaultdict

from app.domain.entities import ConceptOccurrence, Policy, PolicyDocument
from app.domain.value_objects import (
    CONTRACTUAL_DOCUMENT_TYPES,
    ContractStatus,
    DocumentStatus,
    Level,
    PolicyStatus,
)

_PRIORITY = {
    ContractStatus.CONTRACTED: 3,
    ContractStatus.DIVERGENT: 2,
    ContractStatus.NOT_PROVEN: 1,
    ContractStatus.NOT_FOUND: 0,
    ContractStatus.EXCLUDED: 3,
}
_LEVEL_ORDER = [Level.LOW, Level.MEDIUM, Level.HIGH]


def _lowest(levels: list[Level]) -> Level:
    return min(levels, key=_LEVEL_ORDER.index)


def merge_occurrences(occurrences: list[ConceptOccurrence]) -> list[ConceptOccurrence]:
    """Merge occurrences of the same concept found in different documents.

    A contracted coverage and an express exclusion of the same concept become
    DIVERGENT (documentary divergence) instead of silently picking one side.
    """

    grouped: dict[str, list[ConceptOccurrence]] = defaultdict(list)
    for occurrence in occurrences:
        grouped[occurrence.concept_id].append(occurrence)

    merged: list[ConceptOccurrence] = []
    for group in grouped.values():
        statuses = {occurrence.contract_status for occurrence in group}
        winner = max(group, key=lambda occurrence: _PRIORITY[occurrence.contract_status])
        evidence = [item for occurrence in group for item in occurrence.evidence]
        update: dict[str, object] = {
            "evidence": evidence,
            "confidence": _lowest([occurrence.confidence for occurrence in group]),
        }
        if {ContractStatus.CONTRACTED, ContractStatus.EXCLUDED} <= statuses:
            update["contract_status"] = ContractStatus.DIVERGENT
            update["justification"] = (
                "Os documentos divergem: um prevê a cobertura e outro a exclui expressamente."
            )
        with_amount = next((o for o in group if o.amount), None)
        if with_amount and not winner.amount:
            update["amount"] = with_amount.amount
            update["limit_basis"] = with_amount.limit_basis
        merged.append(winner.model_copy(update=update))
    return sorted(merged, key=lambda occurrence: occurrence.concept_id)


def derive_policy_status(
    policy: Policy, documents: list[PolicyDocument], min_confidence: float
) -> tuple[PolicyStatus, list[str]]:
    """Decide READY / ATTENTION / FAILED and the alerts shown to the user."""

    completed = [d for d in documents if d.status == DocumentStatus.COMPLETED]
    failed = [d for d in documents if d.status == DocumentStatus.FAILED]
    if not completed:
        return PolicyStatus.FAILED, ["Nenhum documento pôde ser processado."]

    alerts: list[str] = []
    if not any(d.type in CONTRACTUAL_DOCUMENT_TYPES for d in completed):
        alerts.append(
            "Só há condições gerais ou propostas: a contratação não pode ser comprovada. "
            "Envie a apólice ou a especificação."
        )
    if failed:
        names = ", ".join(d.filename for d in failed)
        alerts.append(f"Documentos não processados: {names}.")
    low = [
        e
        for occurrence in policy.occurrences
        for e in occurrence.evidence
        if e.confidence < min_confidence
    ]
    if low:
        alerts.append(
            f"{len(low)} trecho(s) com baixa confiança de leitura (OCR ou texto divergente)."
        )
    if any(o.contract_status == ContractStatus.DIVERGENT for o in policy.occurrences):
        alerts.append("Há divergência entre documentos da mesma apólice.")
    if not policy.number:
        alerts.append("Número da apólice não identificado.")
    if not policy.occurrences:
        alerts.append("Nenhum conceito do catálogo D&O foi localizado nos documentos.")
    return (PolicyStatus.ATTENTION if alerts else PolicyStatus.READY), alerts
