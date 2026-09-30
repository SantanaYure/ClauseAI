"""The caller's own data (LGPD): what is stored, and erasing all of it."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.presentation.api.dependencies import (
    ApiServices,
    Owner,
    current_owner,
    current_owner_not_revoked,
    get_services,
)
from app.presentation.api.schemas.domain import OwnerDataSummaryResponse

router = APIRouter(prefix="/me", tags=["privacy"], dependencies=[Depends(current_owner)])

Services = Annotated[ApiServices, Depends(get_services)]


@router.get("/data/summary", response_model=OwnerDataSummaryResponse)
async def data_summary(owner: Owner, services: Services) -> OwnerDataSummaryResponse:
    """Counts shown before erasing: policies, their documents and comparisons."""

    summary = await services.owner_data.summary(owner)
    return OwnerDataSummaryResponse(
        policies=summary.policies, documents=summary.documents, comparisons=summary.comparisons
    )


@router.delete("/data", status_code=status.HTTP_204_NO_CONTENT)
async def erase_data(
    owner: Annotated[str, Depends(current_owner_not_revoked)], services: Services
) -> None:
    """Erase every policy, document, comparison and the anonymous account. Idempotent."""

    await services.owner_data.erase(owner)
