"""HTTP error response schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorBody(BaseModel):
    """Public error payload."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    correlation_id: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Standard API error envelope."""

    error: ErrorBody
