"""Access to the use cases assembled by the composition root."""

from dataclasses import dataclass

from fastapi import Request

from app.application.use_cases import ComparisonService, ConceptService, PolicyService
from app.shared.config.settings import Settings


@dataclass(frozen=True, slots=True)
class ApiServices:
    policies: PolicyService
    comparisons: ComparisonService
    concepts: ConceptService


def get_services(request: Request) -> ApiServices:
    services: ApiServices = request.app.state.services
    return services


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", "unknown"))
