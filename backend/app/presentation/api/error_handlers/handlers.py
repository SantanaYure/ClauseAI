"""Global FastAPI exception handlers."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.shared.exceptions import ApplicationError
from app.shared.logging import get_logger

logger = get_logger(__name__)


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def register_exception_handlers(app: object) -> None:
    """Register public exception mappings on a FastAPI application."""

    # Importing the decorator methods here keeps this module focused on
    # translating application errors and avoids framework concerns elsewhere.
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        raise TypeError("register_exception_handlers expects a FastAPI instance")

    @app.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "correlation_id": _correlation_id(request),
                    "details": exc.details,
                }
            },
        )

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
        logger.exception("Unhandled application error", exc_info=exc)
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
