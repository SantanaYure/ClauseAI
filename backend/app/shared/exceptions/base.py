"""Stable exceptions used across application boundaries."""

from typing import Any


class ApplicationError(Exception):
    """Base error with a stable public code and HTTP mapping."""

    default_code = "APPLICATION_ERROR"
    default_status_code = 400

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status_code
        self.details = details


class DomainError(ApplicationError):
    """Business invariant error."""

    default_code = "DOMAIN_ERROR"
    default_status_code = 422


class InfrastructureError(ApplicationError):
    """External system or infrastructure error."""

    default_code = "INFRASTRUCTURE_ERROR"
    default_status_code = 503


class ValidationError(ApplicationError):
    """Input or contract validation error."""

    default_code = "VALIDATION_ERROR"
    default_status_code = 422


class AuthenticationError(ApplicationError):
    """The caller did not prove its identity (missing, invalid, expired or revoked token)."""

    default_code = "AUTH_REQUIRED"
    default_status_code = 401
