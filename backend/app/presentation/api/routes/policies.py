"""Policy endpoints: POST/GET /policies (SPEC-001, SPEC-005, SPEC-006)."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.application.commands import CreatePolicyCommand, UploadedFile
from app.domain.value_objects import DocumentType
from app.presentation.api.dependencies import (
    ApiServices,
    correlation_id,
    get_services,
    get_settings,
)
from app.presentation.api.schemas.domain import (
    Page,
    PolicyCreatedResponse,
    PolicyDetailResponse,
    PolicySummaryResponse,
)
from app.shared.config.settings import Settings
from app.shared.exceptions import ApplicationError

router = APIRouter(prefix="/policies", tags=["policies"])

Services = Annotated[ApiServices, Depends(get_services)]
Correlation = Annotated[str, Depends(correlation_id)]


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=PolicyCreatedResponse)
async def create_policy(
    services: Services,
    correlation: Correlation,
    settings: Annotated[Settings, Depends(get_settings)],
    files: Annotated[list[UploadFile], File(description="PDF, DOCX, JPG ou PNG")],
    document_types: Annotated[list[DocumentType], Form()],
    insurer: Annotated[str | None, Form(max_length=120)] = None,
    name: Annotated[str | None, Form(max_length=120)] = None,
) -> PolicyCreatedResponse:
    """Create a policy with all its documents and start asynchronous processing."""

    if len(document_types) != len(files):
        raise ApplicationError(
            "Informe um tipo de documento para cada arquivo.",
            code="INVALID_DOCUMENT_TYPE",
            status_code=422,
        )
    limit = settings.max_upload_mb * 1024 * 1024
    uploaded = [
        UploadedFile(
            filename=file.filename or "documento",
            declared_content_type=file.content_type,
            data=await file.read(limit + 1),
            document_type=document_type,
        )
        for file, document_type in zip(files, document_types, strict=True)
    ]
    policy = await services.policies.create_policy(
        CreatePolicyCommand(insurer=insurer, name=name, files=uploaded, correlation_id=correlation)
    )
    return PolicyCreatedResponse(
        policy_id=policy.id,
        status=policy.status,
        document_ids=[d.id for d in policy.documents],
        correlation_id=correlation,
    )


@router.get("", response_model=Page[PolicySummaryResponse])
async def list_policies(
    services: Services, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> Page[PolicySummaryResponse]:
    policies = await services.policies.list_policies(limit)
    return Page(items=[PolicySummaryResponse.of(p) for p in policies])


@router.post("/{policy_id}/cancel", response_model=PolicyDetailResponse)
async def cancel_policy(policy_id: str, services: Services) -> PolicyDetailResponse:
    """Cancel asynchronous extraction of a policy (SPEC-003)."""

    return PolicyDetailResponse.of(await services.policies.cancel_policy(policy_id))


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: str, services: Services) -> None:
    """Delete a policy, its evidence and its original files (SPEC-006)."""

    await services.policies.delete_policy(policy_id)


@router.get("/{policy_id}", response_model=PolicyDetailResponse)
async def get_policy(policy_id: str, services: Services) -> PolicyDetailResponse:
    return PolicyDetailResponse.of(await services.policies.get_policy(policy_id))
