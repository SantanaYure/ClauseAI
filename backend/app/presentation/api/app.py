"""FastAPI application factory."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.domain.interfaces.events import EventBus
from app.presentation.api.dependencies import ApiServices
from app.presentation.api.error_handlers import register_exception_handlers
from app.presentation.api.routes.comparisons import router as comparisons_router
from app.presentation.api.routes.concepts import router as concepts_router
from app.presentation.api.routes.health import router as health_router
from app.presentation.api.routes.policies import router as policies_router
from app.shared.config.settings import Settings
from app.shared.logging import configure_logging, get_logger, log_context

logger = get_logger(__name__)


def create_app(
    settings: Settings, event_bus: EventBus, services: ApiServices | None = None
) -> FastAPI:
    """Build the HTTP application from injected runtime dependencies.

    Without `services` only the health check is exposed (foundation mode).
    """

    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        start = getattr(event_bus, "start", None)
        stop = getattr(event_bus, "stop", None)
        if start is not None:
            await start()
        logger.info("Application startup", extra={"app_name": settings.app_name})
        yield
        if stop is not None:
            await stop()
        logger.info("Application shutdown", extra={"app_name": settings.app_name})

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )
    app.state.settings = settings
    app.state.event_bus = event_bus
    app.state.services = services

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        request.state.correlation_id = correlation_id
        with log_context(correlation_id=correlation_id):
            response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    app.include_router(health_router)
    if services is not None:
        for router in (policies_router, comparisons_router, concepts_router):
            app.include_router(router, prefix=settings.api_v1_prefix)
    register_exception_handlers(app)
    return app
