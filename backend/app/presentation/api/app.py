"""FastAPI application factory."""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Protocol

from fastapi import FastAPI

from app.domain.interfaces.events import EventBus
from app.domain.interfaces.ports import IdentityVerifier
from app.presentation.api.dependencies import ApiServices
from app.presentation.api.error_handlers import register_exception_handlers
from app.presentation.api.middleware import (
    install_correlation,
    install_cors,
    install_request_guard,
    install_security_headers,
)
from app.presentation.api.routes.comparisons import router as comparisons_router
from app.presentation.api.routes.concepts import router as concepts_router
from app.presentation.api.routes.health import router as health_router
from app.presentation.api.routes.me import router as me_router
from app.presentation.api.routes.policies import router as policies_router
from app.shared.config.settings import Settings
from app.shared.logging import configure_logging, get_logger

logger = get_logger(__name__)


class BackgroundJob(Protocol):
    """Something started with the application and stopped on shutdown."""

    async def start(self) -> None: ...

    async def stop(self) -> None: ...


def create_app(
    settings: Settings,
    event_bus: EventBus,
    services: ApiServices | None = None,
    identity_verifier: IdentityVerifier | None = None,
    jobs: Sequence[BackgroundJob] = (),
) -> FastAPI:
    """Build the HTTP application from injected runtime dependencies.

    Without `services` only the health check is exposed (foundation mode). Every
    /api/v1 route requires a bearer token checked by `identity_verifier`.
    """

    if services is not None and identity_verifier is None:
        raise ValueError("create_app needs an identity_verifier to expose the API routes")

    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        start = getattr(event_bus, "start", None)
        stop = getattr(event_bus, "stop", None)
        if start is not None:
            await start()
        for job in jobs:
            await job.start()
        logger.info("Application startup")
        yield
        for job in jobs:
            await job.stop()
        if stop is not None:
            await stop()
        logger.info("Application shutdown")

    # Interactive docs reveal the whole surface: only outside production.
    docs = not settings.is_production
    prefix = settings.api_v1_prefix
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=f"{prefix}/docs" if docs else None,
        redoc_url=f"{prefix}/redoc" if docs else None,
        openapi_url=f"{prefix}/openapi.json" if docs else None,
    )
    app.state.settings = settings
    app.state.event_bus = event_bus
    app.state.services = services
    app.state.identity_verifier = identity_verifier

    # Starlette runs the last added middleware first: correlation -> security headers
    # -> CORS -> request guard, so early refusals still carry CORS and correlation ids.
    install_request_guard(app, settings)
    install_cors(app, settings)
    install_security_headers(app, settings)
    install_correlation(app)

    app.include_router(health_router)
    if services is not None:
        for router in (policies_router, comparisons_router, concepts_router, me_router):
            app.include_router(router, prefix=prefix)
    register_exception_handlers(app)
    return app
