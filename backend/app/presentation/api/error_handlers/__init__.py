"""HTTP exception handler public API."""

from app.presentation.api.error_handlers.handlers import register_exception_handlers

__all__ = ["register_exception_handlers"]
