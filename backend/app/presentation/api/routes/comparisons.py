"""Comparison endpoints (SPEC-007 to SPEC-010, SPEC-017)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.application.commands import CreateComparisonCommand
from app.domain.entities import Comparison
from app.presentation.api.dependencies import ApiServices, correlation_id, get_services
from app.presentation.api.schemas.domain import (
    ComparisonCreatedResponse,
    ComparisonCreateRequest,
    ComparisonListItemResponse,
    Page,
)

router = APIRouter(prefix="/comparisons", tags=["comparisons"])

Services = Annotated[ApiServices, Depends(get_services)]


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=ComparisonCreatedResponse)
async def create_comparison(
    body: ComparisonCreateRequest,
    services: Services,
    correlation: Annotated[str, Depends(correlation_id)],
) -> ComparisonCreatedResponse:
    comparison = await services.comparisons.create_comparison(
        CreateComparisonCommand(
            policy_a_id=body.policy_a_id,
            policy_b_id=body.policy_b_id,
            selected_profile=body.selected_profile,
            correlation_id=correlation,
        )
    )
    return ComparisonCreatedResponse(
        comparison_id=comparison.id, status=comparison.status, correlation_id=correlation
    )


@router.get("", response_model=Page[ComparisonListItemResponse])
async def list_comparisons(
    services: Services, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> Page[ComparisonListItemResponse]:
    comparisons = await services.comparisons.list_comparisons(limit)
    return Page(items=[ComparisonListItemResponse.of(c) for c in comparisons])


@router.get("/{comparison_id}", response_model=Comparison)
async def get_comparison(comparison_id: str, services: Services) -> Comparison:
    return await services.comparisons.get_comparison(comparison_id)
