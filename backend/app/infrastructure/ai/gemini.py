"""Gemini adapter: document intake, evidence extraction and normalization
(P-EXTRACT-001, ADR-006, ADR-019)."""

from typing import Any

from google.genai import types
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from app.domain.entities import (
    ConceptOccurrence,
    DocumentIntake,
    Evidence,
    ExtractionResult,
    KnowledgeBase,
)
from app.domain.interfaces.ports import DocumentContent
from app.domain.value_objects import (
    ContractStatus,
    DocumentType,
    ExtractionMethod,
    FileKind,
    Level,
    LimitBasis,
    OccurrenceType,
    TermRelation,
)
from app.shared.exceptions import ApplicationError
from app.infrastructure.ai.gemini_client import GeminiClient
from app.infrastructure.ai.support import (
    InvalidModelOutput,
    load_prompt,
    parse_json_object,
    render,
)

PROMPT_VERSION = "P-EXTRACT-001"
MAX_CATALOG_VARIANTS = 6
_NATIVE_KINDS = {FileKind.SEARCHABLE_PDF, FileKind.DOCX}


class _EvidenceOut(BaseModel):
    page: int = Field(ge=1)
    clause: str
    text: str = Field(min_length=1, max_length=600)
    ocr_confidence: float = Field(default=0.9, ge=0, le=1)


class _OccurrenceOut(BaseModel):
    concept_id: str
    term: str
    occurrence_type: OccurrenceType
    term_relation: TermRelation
    contract_status: ContractStatus
    justification: str | None = None
    confidence: Level = Level.MEDIUM
    alternative_concepts: list[str] = Field(default_factory=list)
    limit_basis: LimitBasis | None = None
    amount: str | None = None
    evidence: list[_EvidenceOut] = Field(default_factory=list)


class _ExtractionOut(BaseModel):
    intake: DocumentIntake
    occurrences: list[_OccurrenceOut] = Field(default_factory=list)


_INTAKE_FIELDS = set(DocumentIntake.model_fields)


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    """Accept the intake fields at the top level, a shape the model sometimes returns."""

    if "intake" in data:
        return data
    intake = {key: data[key] for key in _INTAKE_FIELDS if key in data}
    return {"intake": intake, "occurrences": data.get("occurrences", [])}


def _catalog_text(knowledge_base: KnowledgeBase) -> str:
    lines = [
        f"{c.id} | {c.name} | {'; '.join(c.variants[:MAX_CATALOG_VARIANTS])}"
        for c in knowledge_base.concepts
    ]
    return "\n".join(lines)


_DOCX_NOTE = (
    "Documento Word sem páginas fixas: cada page é um bloco lógico delimitado por quebras "
    "de página, de seção ou por tamanho. Use o número do bloco como page."
)


def _native_text(page_texts: dict[int, str], file_kind: FileKind) -> str:
    pages = [
        f'<page number="{page}">\n{text}\n</page>' for page, text in sorted(page_texts.items())
    ]
    note = f' format="docx" note="{_DOCX_NOTE}"' if file_kind == FileKind.DOCX else ""
    return f"<document{note}>\n" + "\n".join(pages) + "\n</document>"


class GeminiPolicyExtractor:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client
        self._template = load_prompt(PROMPT_VERSION)

    @property
    def model_name(self) -> str:
        return self._client.model

    async def extract(
        self, content: DocumentContent, knowledge_base: KnowledgeBase
    ) -> ExtractionResult:
        document = content.document
        native = document.file_kind in _NATIVE_KINDS and bool(content.page_texts)
        if document.file_kind == FileKind.DOCX and not native:
            raise ApplicationError(
                "O texto do DOCX não foi lido.", code="DOCX_WITHOUT_TEXT", status_code=422
            )
        instructions = render(self._template, catalog=_catalog_text(knowledge_base))
        parts: list[Any] = [instructions]
        if native:
            parts.append(_native_text(content.page_texts, document.file_kind))
        else:
            parts.append(types.Part.from_bytes(data=content.data, mime_type=document.content_type))

        def parse(text: str | None) -> _ExtractionOut:
            try:
                return _ExtractionOut.model_validate(_normalize(parse_json_object(text)))
            except PydanticValidationError as exc:
                raise InvalidModelOutput(str(exc)) from exc

        output = await self._client.generate(parts, PROMPT_VERSION, parse)
        return self._to_domain(output, content, knowledge_base, native)

    def _to_domain(
        self,
        output: _ExtractionOut,
        content: DocumentContent,
        knowledge_base: KnowledgeBase,
        native: bool,
    ) -> ExtractionResult:
        document = content.document
        method = ExtractionMethod.NATIVE if native else ExtractionMethod.MULTIMODAL
        known_ids = {concept.id for concept in knowledge_base.concepts}
        occurrences: list[ConceptOccurrence] = []
        for index, item in enumerate(output.occurrences):
            if item.concept_id not in known_ids:
                continue  # never accept invented concept IDs
            evidence = [
                Evidence(
                    id=f"{document.id}_ev_{index + 1}_{position + 1}",
                    document_id=document.id,
                    document_name=document.filename,
                    page=quote.page,
                    clause=quote.clause.strip() or "Sem numeração",
                    text=quote.text.strip(),
                    method=method,
                    confidence=0.95 if native else round(quote.ocr_confidence, 2),
                )
                for position, quote in enumerate(item.evidence)
            ]
            occurrences.append(
                ConceptOccurrence(
                    concept_id=item.concept_id,
                    term=item.term,
                    occurrence_type=item.occurrence_type,
                    term_relation=item.term_relation,
                    contract_status=item.contract_status,
                    justification=item.justification,
                    evidence=evidence,
                    confidence=item.confidence,
                    alternative_concepts=[c for c in item.alternative_concepts if c in known_ids],
                    limit_basis=item.limit_basis,
                    amount=item.amount,
                )
            )
        intake = output.intake
        if intake.document_type is None:
            intake = intake.model_copy(update={"document_type": DocumentType.OTHER})
        return ExtractionResult(
            intake=intake,
            occurrences=occurrences,
            model=self._client.model,
            prompt_version=PROMPT_VERSION,
        )
