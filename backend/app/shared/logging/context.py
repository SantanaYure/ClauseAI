"""Correlation-aware logging context."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

_log_context: ContextVar[dict[str, str] | None] = ContextVar("log_context", default=None)


def get_log_context() -> dict[str, str]:
    """Return a copy of the current structured log context."""

    return dict(_log_context.get() or {})


@contextmanager
def log_context(**fields: str | None) -> Iterator[None]:
    """Temporarily add non-empty fields to the current log context."""

    current = get_log_context()
    current.update({key: value for key, value in fields.items() if value is not None})
    token: Token[dict[str, str] | None] = _log_context.set(current)
    try:
        yield
    finally:
        _log_context.reset(token)


def set_log_context(**fields: str | None) -> Token[dict[str, str] | None]:
    """Set fields for the current execution context and return a reset token."""

    current = get_log_context()
    current.update({key: value for key, value in fields.items() if value is not None})
    return _log_context.set(current)


def reset_log_context(token: Token[dict[str, str] | None]) -> None:
    """Restore a previous execution context."""

    _log_context.reset(token)
