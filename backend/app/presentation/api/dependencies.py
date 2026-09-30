"""Access to the use cases assembled by the composition root, and caller identity."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from app.application.use_cases import (
    ComparisonService,
    ConceptService,
    OwnerDataService,
    PolicyService,
)
from app.domain.interfaces.ports import IdentityVerifier
from app.shared.config.settings import Settings
from app.shared.exceptions import AuthenticationError
from app.shared.logging import owner_ref, set_log_context


@dataclass(frozen=True, slots=True)
class ApiServices:
    policies: PolicyService
    comparisons: ComparisonService
    concepts: ConceptService
    owner_data: OwnerDataService


def get_services(request: Request) -> ApiServices:
    services: ApiServices = request.app.state.services
    return services


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", "unknown"))


def _bearer_token(request: Request) -> str:
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token or " " in token:
        raise AuthenticationError(
            "Não identificamos este navegador. Recarregue a página.", code="AUTH_REQUIRED"
        )
    return token


async def _authenticate(request: Request, check_revoked: bool) -> str:
    verifier: IdentityVerifier = request.app.state.identity_verifier
    identity = await verifier.verify(_bearer_token(request), check_revoked=check_revoked)
    # The request runs in its own context, so this does not leak to other requests.
    set_log_context(owner_ref=owner_ref(identity.uid))
    return identity.uid


async def current_owner(request: Request) -> str:
    """The anonymous owner id proven by the Firebase ID token (401 otherwise)."""

    return await _authenticate(request, check_revoked=False)


async def current_owner_not_revoked(request: Request) -> str:
    """Like `current_owner`, also refusing revoked tokens (for destructive actions)."""

    return await _authenticate(request, check_revoked=True)


Owner = Annotated[str, Depends(current_owner)]
