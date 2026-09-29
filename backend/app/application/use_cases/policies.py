"""Policy use cases: upload, asynchronous processing and reading
(SPEC-001 to SPEC-006, SPEC-015)."""

import asyncio
from dataclasses import dataclass
from uuid import uuid4

from app.application.commands import CreatePolicyCommand, UploadedFile
from app.application.errors import conflict, invalid, not_found
from app.application.file_types import (
    DOCX_MAX_EXPANSION_RATIO,
    DOCX_MIME,
    FILE_EXTENSIONS,
    PDF_MIME,
    OfficeProblem,
    detect_content_type,
    diagnose_office_problem,
    docx_expanded_size,
)
from app.domain.entities import (
    ConceptOccurrence,
    DocumentIntake,
    KnowledgeBase,
    Policy,
    PolicyDocument,
    utc_now,
)
from app.domain.interfaces.events import Event, EventBus
from app.domain.interfaces.ports import (
    BlobStorage,
    ConceptCatalog,
    DocumentContent,
    DocumentUnreadableError,
    DocxTextReader,
    PdfTextReader,
    PolicyExtractor,
    PolicyRepository,
)
from app.domain.services.guardrails import (
    enforce_contract_rule,
    enforce_evidence_rule,
    verify_evidence,
)
from app.domain.services.policy_aggregation import derive_policy_status, merge_occurrences
from app.domain.value_objects import (
    CONTRACTUAL_DOCUMENT_TYPES,
    DocumentStatus,
    FileKind,
    Level,
    PolicyStatus,
)
from app.shared.exceptions import ApplicationError
from app.shared.logging import get_logger, log_context

POLICY_UPLOADED = "PolicyUploaded"
NOT_IDENTIFIED = "Não identificado"

logger = get_logger(__name__)

_OFFICE_ERRORS = {
    OfficeProblem.PROTECTED: (
        "DOCX_PROTECTED",
        "O arquivo {name} está protegido por senha ou está em formato antigo (.doc). "
        "Remova a proteção e envie novamente como .docx.",
    ),
    OfficeProblem.CORRUPTED: (
        "DOCX_CORRUPTED",
        "O arquivo {name} está corrompido e não pôde ser aberto. Gere o DOCX novamente.",
    ),
}

@dataclass(frozen=True, slots=True)
class UploadLimits:
    max_file_bytes: int
    max_files: int
    min_evidence_confidence: float


def _initial_file_kind(content_type: str) -> FileKind:
    if content_type == PDF_MIME:
        return FileKind.SEARCHABLE_PDF
    return FileKind.DOCX if content_type == DOCX_MIME else FileKind.IMAGE


class PolicyService:
    def __init__(
        self,
        repository: PolicyRepository,
        storage: BlobStorage,
        catalog: ConceptCatalog,
        extractor: PolicyExtractor,
        pdf_reader: PdfTextReader,
        docx_reader: DocxTextReader,
        event_bus: EventBus,
        limits: UploadLimits,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._catalog = catalog
        self._extractor = extractor
        self._pdf_reader = pdf_reader
        self._docx_reader = docx_reader
        self._event_bus = event_bus
        self._limits = limits
        self._running_tasks: dict[str, asyncio.Task[None]] = {}

    # ---------- Commands ----------

    async def _validate(self, files: list[UploadedFile]) -> list[str]:
        if not files:
            raise invalid("INVALID_FILE", "Envie ao menos um arquivo.")
        if len(files) > self._limits.max_files:
            raise invalid(
                "TOO_MANY_FILES", f"Envie no máximo {self._limits.max_files} arquivos por apólice."
            )
        content_types: list[str] = []
        for file in files:
            if not file.data:
                raise invalid("INVALID_FILE", f"Arquivo vazio: {file.filename}.")
            if len(file.data) > self._limits.max_file_bytes:
                raise invalid(
                    "FILE_TOO_LARGE", f"Arquivo acima do limite: {file.filename}.", status_code=413
                )
            detected = detect_content_type(file.data)
            if detected is None:
                raise self._unsupported(file)
            if detected == DOCX_MIME:
                await self._validate_docx(file)
            content_types.append(detected)
        return content_types

    @staticmethod
    def _unsupported(file: UploadedFile) -> ApplicationError:
        problem = diagnose_office_problem(file.data, file.filename)
        if problem is not None:
            code, message = _OFFICE_ERRORS[problem]
            return invalid(code, message.format(name=file.filename), status_code=422)
        return invalid(
            "UNSUPPORTED_MEDIA_TYPE",
            f"Formato não aceito: {file.filename}. Use PDF, DOCX, JPG ou PNG.",
            status_code=415,
        )

    async def _validate_docx(self, file: UploadedFile) -> None:
        """Reject zip bombs and DOCX that cannot be parsed before storing anything."""

        if docx_expanded_size(file.data) > self._limits.max_file_bytes * DOCX_MAX_EXPANSION_RATIO:
            raise invalid(
                "FILE_TOO_LARGE",
                f"O conteúdo do arquivo {file.filename} excede o limite permitido.",
                status_code=413,
            )
        try:
            await asyncio.to_thread(self._docx_reader.read, file.data)
        except DocumentUnreadableError:
            code, message = _OFFICE_ERRORS[OfficeProblem.CORRUPTED]
            raise invalid(code, message.format(name=file.filename), status_code=422) from None

    async def create_policy(self, command: CreatePolicyCommand) -> Policy:
        content_types = await self._validate(command.files)
        policy_id = f"pol_{uuid4().hex[:16]}"
        documents: list[PolicyDocument] = []
        for index, (file, content_type) in enumerate(
            zip(command.files, content_types, strict=True)
        ):
            document_id = f"{policy_id}_doc_{index + 1}"
            extension = FILE_EXTENSIONS[content_type]
            stored = await self._storage.put(
                f"policies/{policy_id}/{document_id}.{extension}", file.data, content_type
            )
            documents.append(
                PolicyDocument(
                    id=document_id,
                    policy_id=policy_id,
                    filename=file.filename[:200],
                    type=file.document_type,
                    content_type=content_type,
                    file_kind=_initial_file_kind(content_type),
                    size_bytes=stored.size_bytes,
                    checksum_sha256=stored.checksum_sha256,
                    storage_key=stored.storage_key,
                    ocr_required=content_type not in (PDF_MIME, DOCX_MIME),
                )
            )
        policy = Policy(
            id=policy_id,
            insurer=(command.insurer or "").strip() or NOT_IDENTIFIED,
            name=(command.name or "").strip() or NOT_IDENTIFIED,
            documents=documents,
            correlation_id=command.correlation_id,
        )
        await self._repository.save(policy)
        await self._event_bus.publish(
            Event.create(POLICY_UPLOADED, command.correlation_id, {"policy_id": policy_id})
        )
        return policy

    # ---------- Worker ----------

    async def handle_policy_uploaded(self, event: Event) -> None:
        await self.process_policy(str(event.payload["policy_id"]))

    async def process_policy(self, policy_id: str) -> None:
        policy = await self._repository.get(policy_id)
        if policy is None or policy.status != PolicyStatus.PROCESSING:
            return  # idempotent: already processed

        current_task = asyncio.current_task()
        if current_task is not None:
            self._running_tasks[policy_id] = current_task

        try:
            knowledge_base = self._catalog.load()
            occurrences: list[ConceptOccurrence] = []
            intakes: list[tuple[PolicyDocument, DocumentIntake]] = []

            with log_context(policy_id=policy_id, correlation_id=policy.correlation_id):
                for document in policy.documents:
                    fresh = await self._repository.get(policy_id)
                    if fresh is None or fresh.status == PolicyStatus.CANCELLED:
                        logger.info("Policy processing aborted: policy cancelled")
                        return

                    try:
                        found, intake = await self._process_document(policy, document, knowledge_base)
                        occurrences.extend(found)
                        intakes.append((document, intake))
                    except ApplicationError as exc:
                        self._fail(document, exc.message)
                    except Exception:
                        logger.exception("Document processing failed")
                        self._fail(document, "Falha inesperada ao processar o documento.")
                    await self._save(policy)

                fresh = await self._repository.get(policy_id)
                if fresh is None or fresh.status == PolicyStatus.CANCELLED:
                    logger.info("Policy processing aborted before final save: policy cancelled")
                    return

                self._apply_intake(policy, intakes)
                policy.occurrences = merge_occurrences(occurrences)
                policy.knowledge_base_version = knowledge_base.version
                status, alerts = derive_policy_status(
                    policy, policy.documents, self._limits.min_evidence_confidence
                )
                policy.alerts = alerts + [
                    f"{document.filename} parece ser do tipo {intake.document_type} "
                    f"(informado: {document.type})."
                    for document, intake in intakes
                    if intake.document_type and intake.document_type not in ("OTHER", document.type)
                ]
                policy.status = status
                await self._save(policy)
                logger.info("Policy processed")
        except asyncio.CancelledError:
            logger.info("Policy processing cancelled via task cancellation")
            raise
        finally:
            self._running_tasks.pop(policy_id, None)

    async def cancel_policy(self, policy_id: str) -> Policy:
        policy = await self.get_policy(policy_id)
        if policy.status != PolicyStatus.PROCESSING:
            raise invalid(
                "POLICY_NOT_PROCESSING",
                "Apenas apólices em processamento podem ser canceladas.",
            )

        task = self._running_tasks.get(policy_id)
        if task is not None and not task.done():
            task.cancel()

        policy.status = PolicyStatus.CANCELLED
        for document in policy.documents:
            if document.status in (
                DocumentStatus.UPLOADED,
                DocumentStatus.PROCESSING,
                DocumentStatus.EXTRACTING,
                DocumentStatus.VALIDATING,
            ):
                document.status = DocumentStatus.CANCELLED
                document.failure = "Extração cancelada pelo usuário."
        cancel_alert = "Extração cancelada pelo usuário."
        if cancel_alert not in policy.alerts:
            policy.alerts.append(cancel_alert)
        await self._save(policy)
        with log_context(policy_id=policy_id, correlation_id=policy.correlation_id):
            logger.info("Policy extraction cancelled")
        return policy

    async def _process_document(
        self, policy: Policy, document: PolicyDocument, knowledge_base: KnowledgeBase
    ) -> tuple[list[ConceptOccurrence], DocumentIntake]:
        document.status = DocumentStatus.EXTRACTING
        await self._save(policy)
        data = await self._storage.get(document.storage_key)

        page_texts: dict[int, str] = {}
        if document.content_type == PDF_MIME:
            pdf = self._pdf_reader.read(data)
            document.pages = max(pdf.page_count, 1)
            document.file_kind = FileKind.SEARCHABLE_PDF if pdf.searchable else FileKind.SCANNED_PDF
            document.ocr_required = not pdf.searchable
            page_texts = pdf.page_texts if pdf.searchable else {}
        elif document.content_type == DOCX_MIME:
            page_texts = await self._read_docx(document, data)
        else:
            document.pages = 1

        result = await self._extractor.extract(
            DocumentContent(document=document, data=data, page_texts=page_texts), knowledge_base
        )
        document.status = DocumentStatus.VALIDATING
        await self._save(policy)

        threshold = self._limits.min_evidence_confidence
        checked: list[ConceptOccurrence] = []
        for occurrence in result.occurrences:
            evidence = [verify_evidence(e, page_texts, threshold) for e in occurrence.evidence]
            occurrence = occurrence.model_copy(update={"evidence": evidence})
            if any(e.confidence < threshold for e in evidence):
                occurrence = occurrence.model_copy(update={"confidence": Level.LOW})
            occurrence = enforce_evidence_rule(occurrence)
            checked.append(enforce_contract_rule(occurrence, document.type))

        low = sum(1 for o in checked for e in o.evidence if e.confidence < threshold)
        document.extraction_quality = (
            Level.LOW if low else (Level.HIGH if not document.ocr_required else Level.MEDIUM)
        )
        document.status = DocumentStatus.COMPLETED
        return checked, result.intake

    async def _read_docx(self, document: PolicyDocument, data: bytes) -> dict[int, str]:
        """DOCX never needs OCR: its text follows the same path as native PDF text."""

        try:
            docx = await asyncio.to_thread(self._docx_reader.read, data)
        except DocumentUnreadableError:
            raise invalid(
                "DOCX_CORRUPTED",
                f"O arquivo {document.filename} está corrompido e não pôde ser lido.",
                status_code=422,
            ) from None
        if not docx.has_text:
            raise invalid(
                "DOCX_WITHOUT_TEXT",
                f"O arquivo {document.filename} não contém texto legível.",
                status_code=422,
            )
        document.pages = docx.page_count
        document.file_kind = FileKind.DOCX
        document.ocr_required = False
        return docx.page_texts

    @staticmethod
    def _fail(document: PolicyDocument, message: str) -> None:
        document.status = DocumentStatus.FAILED
        document.failure = message

    @staticmethod
    def _apply_intake(policy: Policy, intakes: list[tuple[PolicyDocument, DocumentIntake]]) -> None:
        ordered = sorted(intakes, key=lambda item: item[0].type not in CONTRACTUAL_DOCUMENT_TYPES)
        for _document, intake in ordered:
            if policy.insurer == NOT_IDENTIFIED and intake.insurer:
                policy.insurer = intake.insurer
            if policy.name == NOT_IDENTIFIED and intake.policy_name:
                policy.name = intake.policy_name
            policy.number = policy.number or intake.policy_number
            policy.validity = policy.validity or intake.validity

    async def _save(self, policy: Policy) -> None:
        policy.updated_at = utc_now()
        await self._repository.save(policy)

    # ---------- Queries ----------

    async def get_policy(self, policy_id: str) -> Policy:
        policy = await self._repository.get(policy_id)
        if policy is None:
            raise not_found("POLICY_NOT_FOUND", "Apólice não encontrada.")
        return policy

    async def delete_policy(self, policy_id: str) -> None:
        """Delete the policy, its evidence and its original files.

        Comparisons already made stay in the history: they keep a copy of the
        evidence they used. A policy still being processed cannot be deleted, or
        the worker would save it again.
        """

        policy = await self.get_policy(policy_id)
        if policy.status == PolicyStatus.PROCESSING:
            raise conflict(
                "POLICY_PROCESSING",
                "A apólice ainda está em processamento. Aguarde a conclusão para excluí-la.",
            )
        for document in policy.documents:
            await self._storage.delete(document.storage_key)
        await self._repository.delete(policy_id)
        with log_context(policy_id=policy_id, correlation_id=policy.correlation_id):
            logger.info("Policy deleted")

    async def list_policies(self, limit: int) -> list[Policy]:
        return await self._repository.list_recent(limit)
