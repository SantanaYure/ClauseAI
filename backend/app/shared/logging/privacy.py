"""Helpers that keep personal data out of the logs (LGPD).

Logs never carry tokens, file names, insurer names, extracted text or raw
exception messages from third-party libraries: those messages may quote the
document or the provider's answer. The owner appears only as a short hash.
"""

import hashlib
import traceback

OWNER_REF_LENGTH = 12


def owner_ref(owner_id: str) -> str:
    """Stable pseudonymous reference for an owner id."""

    return hashlib.sha256(owner_id.encode("utf-8")).hexdigest()[:OWNER_REF_LENGTH]


def error_fields(exc: BaseException) -> dict[str, str]:
    """Exception type and stack frames, without the exception message."""

    return {
        "error_type": type(exc).__name__,
        "stack": "".join(traceback.format_tb(exc.__traceback__)),
    }
