"""Firestore repositories (ADR-004, docs/architecture/PERSISTENCE_AND_API.md).

Collections: policies/{id} (with documents), policies/{id}/concept_occurrences/{concept_id}
and comparisons/{id}. The Firestore SDK is synchronous, so calls run in a thread.
"""

import asyncio
from typing import Any

from app.domain.entities import Comparison, ConceptOccurrence, Policy


class FirestorePolicyRepository:
    def __init__(self, client: Any) -> None:
        self._collection = client.collection("policies")

    async def save(self, policy: Policy) -> None:
        await asyncio.to_thread(self._save, policy)

    def _save(self, policy: Policy) -> None:
        data = policy.model_dump(mode="json", exclude={"occurrences"})
        reference = self._collection.document(policy.id)
        reference.set(data)
        occurrences = reference.collection("concept_occurrences")
        existing = {snapshot.id for snapshot in occurrences.list_documents()}
        current = {occurrence.concept_id for occurrence in policy.occurrences}
        for occurrence in policy.occurrences:
            occurrences.document(occurrence.concept_id).set(occurrence.model_dump(mode="json"))
        for stale in existing - current:
            occurrences.document(stale).delete()

    async def get(self, policy_id: str) -> Policy | None:
        return await asyncio.to_thread(self._get, policy_id)

    def _get(self, policy_id: str) -> Policy | None:
        reference = self._collection.document(policy_id)
        snapshot = reference.get()
        if not snapshot.exists:
            return None
        occurrences = [
            ConceptOccurrence.model_validate(item.to_dict())
            for item in reference.collection("concept_occurrences").stream()
        ]
        return Policy.model_validate({**snapshot.to_dict(), "occurrences": occurrences})

    async def list_recent(self, limit: int) -> list[Policy]:
        return await asyncio.to_thread(self._list, limit)

    def _list(self, limit: int) -> list[Policy]:
        query = self._collection.order_by("created_at", direction="DESCENDING").limit(limit)
        policies: list[Policy] = []
        for snapshot in query.stream():
            policy = self._get(snapshot.id)
            if policy:
                policies.append(policy)
        return policies


class FirestoreComparisonRepository:
    def __init__(self, client: Any) -> None:
        self._collection = client.collection("comparisons")

    async def save(self, comparison: Comparison) -> None:
        data = comparison.model_dump(mode="json")
        await asyncio.to_thread(self._collection.document(comparison.id).set, data)

    async def get(self, comparison_id: str) -> Comparison | None:
        snapshot = await asyncio.to_thread(self._collection.document(comparison_id).get)
        return Comparison.model_validate(snapshot.to_dict()) if snapshot.exists else None

    async def list_recent(self, limit: int) -> list[Comparison]:
        def run() -> list[Comparison]:
            query = self._collection.order_by("created_at", direction="DESCENDING").limit(limit)
            return [Comparison.model_validate(item.to_dict()) for item in query.stream()]

        return await asyncio.to_thread(run)
