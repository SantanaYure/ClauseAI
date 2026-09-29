"""Public error catalog used by the use cases (SPEC-001, SPEC-006, SPEC-007, SPEC-011)."""

from app.shared.exceptions import ApplicationError


def not_found(code: str, message: str) -> ApplicationError:
    return ApplicationError(message, code=code, status_code=404)


def conflict(code: str, message: str) -> ApplicationError:
    return ApplicationError(message, code=code, status_code=409)


def invalid(code: str, message: str, status_code: int = 400) -> ApplicationError:
    return ApplicationError(message, code=code, status_code=status_code)
