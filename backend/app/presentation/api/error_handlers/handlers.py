"""Global FastAPI exception handlers."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.shared.exceptions import ApplicationError
from app.shared.logging import error_fields, get_logger, log_context

logger = get_logger(__name__)


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def application_error_response(request: Request, exc: ApplicationError) -> JSONResponse:
    """The standard error envelope; also used by middleware that answers before routing."""

    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "correlation_id": _correlation_id(request),
                "details": exc.details,
            }
        },
    )


def register_exception_handlers(app: object) -> None:
    """Register public exception mappings on a FastAPI application."""

    # Importing the decorator methods here keeps this module focused on
    # translating application errors and avoids framework concerns elsewhere.
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        raise TypeError("register_exception_handlers expects a FastAPI instance")

    @app.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError) -> JSONResponse:
        return application_error_response(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "REQUEST_VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "correlation_id": _correlation_id(request),
                    "details": {"errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        with log_context(**error_fields(exc)):
            logger.error("Unhandled application error")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "correlation_id": _correlation_id(request),
                }
            },
        )
