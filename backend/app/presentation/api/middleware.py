"""HTTP hardening: CORS, early request guard, security headers and correlation ids."""

import re
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.presentation.api.error_handlers import application_error_response
from app.shared.config.settings import Settings
from app.shared.exceptions import ApplicationError, AuthenticationError
from app.shared.logging import log_context

CORRELATION_HEADER = "X-Correlation-ID"
# Anything else is replaced: the header is echoed back and written to the logs.
VALID_CORRELATION_ID = re.compile(r"[A-Za-z0-9-]{1,64}")

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
}
_HSTS = "max-age=63072000; includeSubDomains"
# Room for multipart boundaries, part headers and the small form fields.
MULTIPART_OVERHEAD_BYTES = 1024 * 1024

Handler = Callable[[Request], Awaitable[Response]]


def install_cors(app: FastAPI, settings: Settings) -> None:
    # The API authenticates with a bearer token, never with cookies: no credentials.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", CORRELATION_HEADER],
        expose_headers=[CORRELATION_HEADER],
    )


def _has_bearer_token(request: Request) -> bool:
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    return scheme.lower() == "bearer" and bool(token.strip())


def _declared_length(request: Request) -> int | None:
    try:
        return int(request.headers["Content-Length"])
    except (KeyError, ValueError):
        return None


def install_request_guard(app: FastAPI, settings: Settings) -> None:
    """Refuse API requests without a bearer token or with an oversized body early.

    FastAPI parses the multipart body before running the auth dependency, so without
    this an anonymous client could make the server read and spool a large upload. The
    token itself is still verified by the route dependency. Must be installed before
    `install_cors`, so CORS (outer) adds its headers to these responses too.
    """

    prefix = settings.api_v1_prefix
    public_paths = {f"{prefix}/docs", f"{prefix}/docs/oauth2-redirect", f"{prefix}/redoc"}
    public_paths.add(f"{prefix}/openapi.json")
    max_body = (
        settings.max_files_per_policy * settings.max_upload_mb * 1024 * 1024
        + MULTIPART_OVERHEAD_BYTES
    )

    @app.middleware("http")
    async def request_guard(request: Request, call_next: Handler) -> Response:
        path = request.url.path
        guarded = (
            request.method != "OPTIONS"
            and (path == prefix or path.startswith(f"{prefix}/"))
            and path not in public_paths
        )
        if guarded:
            if not _has_bearer_token(request):
                return application_error_response(
                    request,
                    AuthenticationError(
                        "Não identificamos este navegador. Recarregue a página.",
                        code="AUTH_REQUIRED",
                    ),
                )
            length = _declared_length(request)
            if length is not None and length > max_body:
                return application_error_response(
                    request,
                    ApplicationError(
                        f"O envio passa do limite de {settings.max_files_per_policy} arquivos "
                        f"de até {settings.max_upload_mb} MB.",
                        code="FILE_TOO_LARGE",
                        status_code=413,
                    ),
                )
        return await call_next(request)


def install_security_headers(app: FastAPI, settings: Settings) -> None:
    api_prefix = settings.api_v1_prefix

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Handler) -> Response:
        response = await call_next(request)
        response.headers.update(_SECURITY_HEADERS)
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = _HSTS
        if request.url.path.startswith(api_prefix):
            response.headers["Cache-Control"] = "no-store"
        return response


def install_correlation(app: FastAPI) -> None:
    @app.middleware("http")
    async def correlation(request: Request, call_next: Handler) -> Response:
        received = request.headers.get(CORRELATION_HEADER, "")
        correlation_id = received if VALID_CORRELATION_ID.fullmatch(received) else str(uuid4())
        request.state.correlation_id = correlation_id
        with log_context(correlation_id=correlation_id):
            response = await call_next(request)
        response.headers[CORRELATION_HEADER] = correlation_id
        return response
