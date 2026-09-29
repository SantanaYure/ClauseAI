"""Composition root for the ClauseAI API (docs/architecture/MODULE_STRUCTURE.md, section 7)."""

from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from app.application.use_cases import (
    COMPARISON_REQUESTED,
    POLICY_UPLOADED,
    ComparisonService,
    ConceptService,
    PolicyService,
    UploadLimits,
)
from app.domain.interfaces.ports import BlobStorage, ComparisonRepository, PolicyRepository
from app.domain.services.scoring import ScoringParameters
from app.infrastructure.ai.gemini import GeminiPolicyExtractor
from app.infrastructure.ai.groq import GroqClient, GroqConceptAssessor, GroqSummaryWriter
from app.infrastructure.events import QueuedEventBus
from app.infrastructure.knowledge_base import JsonConceptCatalog
from app.infrastructure.pdf import PypdfTextReader
from app.infrastructure.persistence import (
    InMemoryComparisonRepository,
    InMemoryPolicyRepository,
)
from app.infrastructure.storage import LocalBlobStorage
from app.presentation.api.app import create_app
from app.presentation.api.dependencies import ApiServices
from app.shared.config.settings import Settings, get_settings


class ConfigurationError(RuntimeError):
    """Raised at startup when required environment variables are missing."""


def _firebase_app(settings: Settings) -> Any:
    import firebase_admin
    from firebase_admin import credentials

    if "clauseai" in firebase_admin._apps:  # already initialized in this process
        return firebase_admin.get_app("clauseai")
    if settings.firebase_credentials_path:
        credential = credentials.Certificate(settings.firebase_credentials_path)
    else:
        credential = credentials.Certificate(
            {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "client_email": settings.firebase_client_email,
                "private_key": settings.firebase_private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )
    options = (
        {"storageBucket": settings.firebase_storage_bucket}
        if settings.firebase_storage_bucket
        else None
    )
    return firebase_admin.initialize_app(credential, options, name="clauseai")


def _repositories(
    settings: Settings, firebase: Any
) -> tuple[PolicyRepository, ComparisonRepository]:
    if settings.persistence_backend == "memory":
        return InMemoryPolicyRepository(), InMemoryComparisonRepository()
    from firebase_admin import firestore

    from app.infrastructure.persistence import (
        FirestoreComparisonRepository,
        FirestorePolicyRepository,
    )

    client = firestore.client(firebase)
    return FirestorePolicyRepository(client), FirestoreComparisonRepository(client)


def _storage(settings: Settings, firebase: Any) -> BlobStorage:
    if settings.storage_backend == "local":
        return LocalBlobStorage(Path(settings.local_storage_dir))
    from firebase_admin import storage

    from app.infrastructure.storage import FirebaseBlobStorage

    return FirebaseBlobStorage(storage.bucket(app=firebase))


def build_application(settings: Settings) -> FastAPI:
    missing = settings.missing_required()
    if missing:
        raise ConfigurationError(
            "Configuração incompleta no backend/.env. Preencha: " + ", ".join(missing)
        )

    event_bus = QueuedEventBus(workers=settings.worker_concurrency)
    uses_firebase = "firebase" in (settings.persistence_backend, settings.storage_backend)
    firebase = _firebase_app(settings) if uses_firebase else None
    policies, comparisons = _repositories(settings, firebase)
    storage = _storage(settings, firebase)

    catalog = JsonConceptCatalog()
    groq = GroqClient(
        api_key=settings.groq_api_key or "",
        model=settings.groq_model,
        timeout_seconds=settings.ai_timeout_seconds,
        max_attempts=settings.ai_max_attempts,
        batch_size=settings.groq_batch_size,
        reasoning_effort=settings.groq_reasoning_effort,
    )
    policy_service = PolicyService(
        repository=policies,
        storage=storage,
        catalog=catalog,
        extractor=GeminiPolicyExtractor(
            api_key=settings.gemini_api_key or "",
            model=settings.gemini_model,
            timeout_seconds=settings.ai_timeout_seconds,
            max_attempts=settings.ai_max_attempts,
        ),
        pdf_reader=PypdfTextReader(),
        event_bus=event_bus,
        limits=UploadLimits(
            max_file_bytes=settings.max_upload_mb * 1024 * 1024,
            max_files=settings.max_files_per_policy,
            min_evidence_confidence=settings.min_evidence_confidence,
        ),
    )
    comparison_service = ComparisonService(
        comparisons=comparisons,
        policies=policies,
        catalog=catalog,
        assessor=GroqConceptAssessor(groq),
        summary_writer=GroqSummaryWriter(groq),
        event_bus=event_bus,
        parameters=ScoringParameters(
            profile_multiplier=Decimal(str(settings.profile_multiplier)),
            close_score_threshold=Decimal(str(settings.close_score_threshold)),
            min_completeness=Decimal(str(settings.min_completeness)),
            ocr_min_confidence=settings.min_evidence_confidence,
        ),
    )
    event_bus.subscribe(POLICY_UPLOADED, policy_service.handle_policy_uploaded)
    event_bus.subscribe(COMPARISON_REQUESTED, comparison_service.handle_comparison_requested)

    services = ApiServices(
        policies=policy_service,
        comparisons=comparison_service,
        concepts=ConceptService(catalog, policies),
    )
    return create_app(settings=settings, event_bus=event_bus, services=services)


app = build_application(get_settings())
