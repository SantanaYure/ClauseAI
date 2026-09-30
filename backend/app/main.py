"""Composition root for the ClauseAI API (docs/architecture/MODULE_STRUCTURE.md, section 7)."""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from app.application.quotas import QuotaGuard, QuotaLimits
from app.application.use_cases import (
    COMPARISON_REQUESTED,
    POLICY_UPLOADED,
    ComparisonService,
    ConceptService,
    OwnerDataService,
    PolicyService,
    RetentionSweeper,
    UploadLimits,
)
from app.domain.interfaces.ports import (
    AccountRemover,
    BlobStorage,
    ComparisonRepository,
    ConceptAssessor,
    IdentityVerifier,
    PolicyExtractor,
    PolicyRepository,
    SummaryWriter,
)
from app.domain.services.scoring import ScoringParameters
from app.infrastructure.ai.assessment import GeminiConceptAssessor, GeminiSummaryWriter
from app.infrastructure.ai.gemini import GeminiPolicyExtractor
from app.infrastructure.ai.gemini_client import GeminiClient
from app.infrastructure.ai.local import (
    LocalConceptAssessor,
    LocalPolicyExtractor,
    LocalSummaryWriter,
)
from app.infrastructure.auth import (
    FakeAccountRemover,
    FakeIdentityVerifier,
    FirebaseAccountRemover,
    FirebaseIdentityVerifier,
)
from app.infrastructure.events import QueuedEventBus
from app.infrastructure.firebase import firebase_app
from app.infrastructure.knowledge_base import JsonConceptCatalog
from app.infrastructure.pdf import PypdfTextReader
from app.infrastructure.persistence import (
    InMemoryComparisonRepository,
    InMemoryPolicyRepository,
)
from app.infrastructure.quotas import SlidingWindowRateLimiter
from app.infrastructure.scheduling import PeriodicJob
from app.infrastructure.storage import LocalBlobStorage
from app.infrastructure.word import PythonDocxTextReader
from app.presentation.api.app import create_app
from app.presentation.api.dependencies import ApiServices
from app.shared.config.settings import Settings, get_settings


class ConfigurationError(RuntimeError):
    """Raised at startup when required environment variables are missing."""


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


def _identity(settings: Settings, firebase: Any) -> tuple[IdentityVerifier, AccountRemover]:
    if settings.auth_backend == "fake":
        return FakeIdentityVerifier(), FakeAccountRemover()
    return (
        FirebaseIdentityVerifier(firebase, settings.auth_clock_skew_seconds),
        FirebaseAccountRemover(firebase),
    )


def _ai_components(
    settings: Settings,
) -> tuple[PolicyExtractor, ConceptAssessor, SummaryWriter]:
    if settings.ai_provider == "local":
        return LocalPolicyExtractor(), LocalConceptAssessor(), LocalSummaryWriter()
    gemini = GeminiClient(
        api_key=settings.gemini_api_key or "",
        model=settings.gemini_model,
        timeout_seconds=settings.ai_timeout_seconds,
        max_attempts=settings.ai_max_attempts,
        assessment_batch_size=settings.assessment_batch_size,
    )
    return (
        GeminiPolicyExtractor(gemini, settings.extraction_pages_per_call),
        GeminiConceptAssessor(gemini),
        GeminiSummaryWriter(gemini),
    )


def _quotas(settings: Settings) -> QuotaGuard:
    return QuotaGuard(
        SlidingWindowRateLimiter(),
        QuotaLimits(
            max_active_policies=settings.max_active_policies_per_owner,
            uploads_per_hour=settings.uploads_per_hour,
            comparisons_per_hour=settings.comparisons_per_hour,
        ),
    )


def build_application(settings: Settings) -> FastAPI:
    missing = settings.missing_required()
    if missing:
        raise ConfigurationError(
            "Configuração incompleta no backend/.env. Preencha: "
            + ", ".join(missing)
            + ". Para desenvolvimento sem serviços externos use AI_PROVIDER=local, "
            "PERSISTENCE_BACKEND=memory, STORAGE_BACKEND=local e AUTH_BACKEND=fake."
        )

    event_bus = QueuedEventBus(workers=settings.worker_concurrency)
    firebase = firebase_app(settings) if settings.uses_firebase else None
    policies, comparisons = _repositories(settings, firebase)
    storage = _storage(settings, firebase)
    identity_verifier, account_remover = _identity(settings, firebase)
    quotas = _quotas(settings)

    catalog = JsonConceptCatalog()
    extractor, assessor, summary_writer = _ai_components(settings)
    policy_service = PolicyService(
        repository=policies,
        storage=storage,
        catalog=catalog,
        extractor=extractor,
        pdf_reader=PypdfTextReader(),
        docx_reader=PythonDocxTextReader(),
        event_bus=event_bus,
        limits=UploadLimits(
            max_file_bytes=settings.max_upload_mb * 1024 * 1024,
            max_files=settings.max_files_per_policy,
            min_evidence_confidence=settings.min_evidence_confidence,
        ),
        quotas=quotas,
        retention=timedelta(hours=settings.retention_hours),
    )
    comparison_service = ComparisonService(
        comparisons=comparisons,
        policies=policies,
        catalog=catalog,
        assessor=assessor,
        summary_writer=summary_writer,
        event_bus=event_bus,
        parameters=ScoringParameters(
            profile_multiplier=Decimal(str(settings.profile_multiplier)),
            close_score_threshold=Decimal(str(settings.close_score_threshold)),
            min_completeness=Decimal(str(settings.min_completeness)),
            ocr_min_confidence=settings.min_evidence_confidence,
        ),
        quotas=quotas,
    )
    event_bus.subscribe(POLICY_UPLOADED, policy_service.handle_policy_uploaded)
    event_bus.subscribe(COMPARISON_REQUESTED, comparison_service.handle_comparison_requested)

    services = ApiServices(
        policies=policy_service,
        comparisons=comparison_service,
        concepts=ConceptService(catalog, policies),
        owner_data=OwnerDataService(
            policy_service=policy_service,
            comparison_service=comparison_service,
            policies=policies,
            comparisons=comparisons,
            storage=storage,
            accounts=account_remover,
        ),
    )
    sweeper = RetentionSweeper(policies, comparisons, storage)
    retention_job = PeriodicJob(
        "retention-sweep", sweeper.sweep, settings.retention_sweep_minutes * 60
    )
    return create_app(
        settings=settings,
        event_bus=event_bus,
        services=services,
        identity_verifier=identity_verifier,
        jobs=[retention_job],
    )


_application: FastAPI | None = None


def __getattr__(name: str) -> FastAPI:
    """Build `app` on first access, so importing this module needs no configuration."""

    global _application
    if name != "app":
        raise AttributeError(name)
    if _application is None:
        _application = build_application(get_settings())
    return _application
