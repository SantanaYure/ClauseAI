"""Deterministic AI stand-ins for local development (AI_PROVIDER=local).

They make the API usable in a browser without any external service. They read
only the native text of the document (PDF text layer or DOCX), quote it
literally and never call a model. Scanned PDFs and images yield no occurrences.
Never use them in production (`Settings.missing_required` refuses that).
"""

import re

from app.domain.entities import (
    AssessmentDecision,
    ConceptAssessment,
    ConceptOccurrence,
    DocumentIntake,
    Evidence,
    ExecutiveSummary,
    ExtractionResult,
    KnowledgeBase,
)
from app.domain.interfaces.ports import AssessmentRequest, DocumentContent
from app.domain.services.text import normalize_text
from app.domain.value_objects import (
    CONTRACTUAL_DOCUMENT_TYPES,
    ContractStatus,
    ExtractionMethod,
    Level,
    OccurrenceType,
    TermRelation,
)

MODEL_NAME = "local-deterministic"
PROMPT_VERSION = "local"
_QUOTE_CHARS = 280
_CLAUSE = re.compile(r"^\s*(\d+(?:\.\d+)*)[.)]?\s")


def _clause_of(line: str) -> str:
    match = _CLAUSE.match(line)
    return match.group(1) if match else "Sem numeração"


class LocalPolicyExtractor:
    """Finds catalog variants in the native text and quotes the surrounding text."""

    @property
    def model_name(self) -> str:
        return MODEL_NAME

    async def extract(
        self, content: DocumentContent, knowledge_base: KnowledgeBase
    ) -> ExtractionResult:
        document = content.document
        status = (
            ContractStatus.CONTRACTED
            if document.type in CONTRACTUAL_DOCUMENT_TYPES
            else ContractStatus.NOT_PROVEN
        )
        occurrences: list[ConceptOccurrence] = []
        for concept in knowledge_base.concepts:
            evidence = self._evidence(content, concept.variants, document.id, concept.id)
            if not evidence:
                continue
            occurrences.append(
                ConceptOccurrence(
                    concept_id=concept.id,
                    term=concept.name,
                    occurrence_type=OccurrenceType.REFERENCE,
                    term_relation=TermRelation.LEXICAL_VARIANT,
                    contract_status=status,
                    justification="Termo localizado por busca textual (modo de desenvolvimento).",
                    evidence=evidence,
                    confidence=Level.MEDIUM,
                )
            )
        intake = DocumentIntake(document_type=document.type, language="pt-BR")
        return ExtractionResult(
            intake=intake, occurrences=occurrences, model=MODEL_NAME, prompt_version=PROMPT_VERSION
        )

    @staticmethod
    def _evidence(
        content: DocumentContent, variants: list[str], document_id: str, concept_id: str
    ) -> list[Evidence]:
        wanted = [normalize_text(variant) for variant in variants]
        for page, text in sorted(content.page_texts.items()):
            for line in text.splitlines():
                normalized = normalize_text(line)
                if any(variant and variant in normalized for variant in wanted):
                    return [
                        Evidence(
                            id=f"{document_id}_ev_{concept_id}",
                            document_id=document_id,
                            document_name=content.document.filename,
                            page=page,
                            clause=_clause_of(line),
                            text=" ".join(line.split())[:_QUOTE_CHARS],
                            method=ExtractionMethod.NATIVE,
                            confidence=0.95,
                        )
                    ]
        return []


class LocalConceptAssessor:
    model_name = MODEL_NAME

    async def assess(self, requests: list[AssessmentRequest]) -> list[ConceptAssessment]:
        def decide(side: dict[str, object]) -> AssessmentDecision:
            contracted = side.get("contract_status") == ContractStatus.CONTRACTED
            return AssessmentDecision(
                base_result=1.0 if contracted else 0.25,
                adjustment_factor=1.0,
                justification=None if contracted else "Somente menção; contratação não provada.",
            )

        return [
            ConceptAssessment(
                concept_id=r.concept_id,
                a=decide(r.policy_a),
                b=decide(r.policy_b),
                main_difference="",
            )
            for r in requests
        ]


class LocalSummaryWriter:
    async def write_conclusion(self, summary: ExecutiveSummary, facts: dict[str, object]) -> str:
        return summary.conclusion
