"""Infrastructure health endpoint."""

from fastapi import APIRouter

from app.presentation.api.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Report that the API process is accepting requests."""

    return HealthResponse(status="ok")
