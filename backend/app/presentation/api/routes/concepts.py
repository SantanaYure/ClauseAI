"""Concept catalog and query endpoints (SPEC-018)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.domain.entities import Concept
from app.presentation.api.dependencies import ApiServices, Owner, current_owner, get_services
from app.presentation.api.schemas.domain import (
    OccurrenceMatchResponse,
    Page,
    QueryAnswerResponse,
    QueryRequest,
)

# The catalog itself is public knowledge, but the whole router requires an identity
# (one rule for every /api/v1 route).
router = APIRouter(tags=["concepts"], dependencies=[Depends(current_owner)])

Services = Annotated[ApiServices, Depends(get_services)]


@router.get("/concepts", response_model=Page[Concept])
async def list_concepts(
    services: Services, limit: Annotated[int, Query(ge=1, le=100)] = 100
) -> Page[Concept]:
    return Page(items=services.concepts.list_concepts()[:limit])


@router.get("/concepts/{concept_id}", response_model=Concept)
async def get_concept(concept_id: str, services: Services) -> Concept:
    return services.concepts.get_concept(concept_id)


@router.get("/concepts/{concept_id}/occurrences", response_model=Page[OccurrenceMatchResponse])
async def concept_occurrences(
    concept_id: str,
    owner: Owner,
    services: Services,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> Page[OccurrenceMatchResponse]:
    matches = await services.concepts.occurrences(owner, concept_id, limit)
    return Page(
        items=[OccurrenceMatchResponse(policy=m.policy, occurrence=m.occurrence) for m in matches]
    )


@router.post("/queries", response_model=QueryAnswerResponse)
async def ask(body: QueryRequest, owner: Owner, services: Services) -> QueryAnswerResponse:
    answer = await services.concepts.ask(owner, body.question.strip())
    return QueryAnswerResponse(
        question=answer.question,
        concept=answer.concept,
        answer=answer.answer,
        matches=[
            OccurrenceMatchResponse(policy=m.policy, occurrence=m.occurrence)
            for m in answer.matches
        ],
        guidance=answer.guidance,
    )
