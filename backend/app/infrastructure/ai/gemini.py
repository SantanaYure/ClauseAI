"""Gemini adapter: document intake, evidence extraction and normalization
(P-EXTRACT-001, ADR-006, ADR-019)."""

from typing import Any

import httpx
from google import genai
from google.genai import errors as genai_errors
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
from app.infrastructure.ai.support import (
    InvalidModelOutput,
    RateLimitedError,
    TransientProviderError,
    call_with_retries,
    load_prompt,
    parse_json_object,
    render,
    retry_after_seconds,
)

PROMPT_VERSION = "P-EXTRACT-001"
MAX_CATALOG_VARIANTS = 6


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


def _native_text(page_texts: dict[int, str]) -> str:
    pages = [
        f'<page number="{page}">\n{text}\n</page>' for page, text in sorted(page_texts.items())
    ]
    return "<document>\n" + "\n".join(pages) + "\n</document>"


class GeminiPolicyExtractor:
    def __init__(self, api_key: str, model: str, timeout_seconds: float, max_attempts: int) -> None:
        self._client = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000))
        )
        self._model = model
        self._max_attempts = max_attempts
        self._system = load_prompt("P-SYSTEM-001")
        self._template = load_prompt(PROMPT_VERSION)

    @property
    def model_name(self) -> str:
        return self._model

    async def extract(
        self, content: DocumentContent, knowledge_base: KnowledgeBase
    ) -> ExtractionResult:
        document = content.document
        native = document.file_kind == FileKind.SEARCHABLE_PDF and bool(content.page_texts)
        instructions = render(self._template, catalog=_catalog_text(knowledge_base))
        parts: list[Any] = [instructions]
        if native:
            parts.append(_native_text(content.page_texts))
        else:
            parts.append(types.Part.from_bytes(data=content.data, mime_type=document.content_type))

        async def run() -> _ExtractionOut:
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=parts,
                    config=types.GenerateContentConfig(
                        system_instruction=self._system,
                        temperature=0,
                        response_mime_type="application/json",
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True
                        ),
                    ),
                )
            except (genai_errors.ServerError, httpx.TimeoutException, httpx.TransportError) as exc:
                raise TransientProviderError(str(exc)) from exc
            except genai_errors.ClientError as exc:
                if getattr(exc, "code", None) == 429:
                    raise RateLimitedError(str(exc), retry_after_seconds(None, str(exc))) from exc
                if getattr(exc, "code", None) == 408:
                    raise TransientProviderError(str(exc)) from exc
                raise
            try:
                return _ExtractionOut.model_validate(_normalize(parse_json_object(response.text)))
            except PydanticValidationError as exc:
                raise InvalidModelOutput(str(exc)) from exc

        output = await call_with_retries(
            run,
            provider="gemini",
            model=self._model,
            prompt_version=PROMPT_VERSION,
            max_attempts=self._max_attempts,
        )
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
            intake=intake, occurrences=occurrences, model=self._model, prompt_version=PROMPT_VERSION
        )
