"""Concept catalog and evidence-only queries (SPEC-018).

Occurrences and answers consider only the caller's own policies still within retention.
"""

from dataclasses import dataclass

from app.application.errors import not_found
from app.domain.entities import Concept, ConceptOccurrence, Policy, PolicyRef, utc_now
from app.domain.interfaces.ports import ConceptCatalog, PolicyRepository
from app.domain.services.text import normalize_text, resolve_concept
from app.domain.value_objects import (
    BROKER_GUIDANCE,
    COMPARABLE_POLICY_STATUSES,
    ContractStatus,
)

SCAN_LIMIT = 200

_STATUS_TEXT = {
    ContractStatus.CONTRACTED: "contratada",
    ContractStatus.NOT_PROVEN: "não comprovado",
    ContractStatus.NOT_FOUND: "não localizado",
    ContractStatus.EXCLUDED: "excluído",
    ContractStatus.DIVERGENT: "divergente",
}


@dataclass(frozen=True, slots=True)
class OccurrenceMatch:
    policy: PolicyRef
    occurrence: ConceptOccurrence | None


@dataclass(frozen=True, slots=True)
class QueryAnswer:
    question: str
    concept: Concept | None
    answer: str
    matches: list[OccurrenceMatch]
    guidance: bool


class ConceptService:
    def __init__(self, catalog: ConceptCatalog, policies: PolicyRepository) -> None:
        self._catalog = catalog
        self._policies = policies

    def list_concepts(self) -> list[Concept]:
        return self._catalog.load().concepts

    def get_concept(self, concept_id: str) -> Concept:
        concept = self._catalog.load().get(concept_id)
        if concept is None:
            raise not_found("CONCEPT_NOT_FOUND", "Conceito não encontrado.")
        return concept

    async def _owned_policies(self, owner_id: str) -> list[Policy]:
        now = utc_now()
        policies = await self._policies.list_recent(owner_id, SCAN_LIMIT)
        return [policy for policy in policies if not policy.is_expired(now)]

    async def occurrences(
        self, owner_id: str, concept_id: str, limit: int
    ) -> list[OccurrenceMatch]:
        self.get_concept(concept_id)
        matches: list[OccurrenceMatch] = []
        for policy in await self._owned_policies(owner_id):
            for occurrence in policy.occurrences:
                if occurrence.concept_id == concept_id:
                    ref = PolicyRef(id=policy.id, insurer=policy.insurer, name=policy.name)
                    matches.append(OccurrenceMatch(policy=ref, occurrence=occurrence))
        return matches[:limit]

    async def ask(self, owner_id: str, question: str) -> QueryAnswer:
        """Answer only with stored evidence; otherwise state the limit of the base."""

        concept = resolve_concept(question, self._catalog.load().concepts)
        if concept is None:
            return QueryAnswer(
                question=question,
                concept=None,
                answer=(
                    "Não encontrei esse tema no catálogo de conceitos D&O nem nas evidências "
                    f"armazenadas. {BROKER_GUIDANCE}"
                ),
                matches=[],
                guidance=True,
            )

        policies = [
            p
            for p in await self._owned_policies(owner_id)
            if p.status in COMPARABLE_POLICY_STATUSES
        ]
        normalized = normalize_text(question)
        mentioned = [
            p
            for p in policies
            if any(
                len(word) > 3 and word in normalized
                for word in normalize_text(p.insurer.replace("Seguradora", "")).split()
            )
        ]
        matches = [
            OccurrenceMatch(
                policy=PolicyRef(id=p.id, insurer=p.insurer, name=p.name),
                occurrence=next((o for o in p.occurrences if o.concept_id == concept.id), None),
            )
            for p in (mentioned or policies)
        ]
        guidance = not matches or any(
            m.occurrence is None or m.occurrence.contract_status != ContractStatus.CONTRACTED
            for m in matches
        )
        parts = [
            f"{m.policy.insurer}: "
            + (_STATUS_TEXT[m.occurrence.contract_status] if m.occurrence else "não localizado")
            for m in matches
        ]
        answer = f"{concept.name} — " + (
            "; ".join(parts) if parts else "nenhuma apólice processada"
        )
        return QueryAnswer(
            question=question,
            concept=concept,
            answer=f"{answer}.{' ' + BROKER_GUIDANCE if guidance else ''}",
            matches=matches,
            guidance=guidance,
        )
