"""Health check response schema."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Minimal health response required by the MVP foundation."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
