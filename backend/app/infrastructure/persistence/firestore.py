"""Firestore repositories (ADR-004, docs/architecture/PERSISTENCE_AND_API.md).

Collections: policies/{id} (with documents), policies/{id}/concept_occurrences/{concept_id}
and comparisons/{id}. Every document carries `owner_id` and `expires_at` (a native
timestamp). The Firestore TTL policy is not active: the RetentionSweeper deletes expired
documents, and reads already hide them from their owner in the meantime.
Records without an owner (created before owner isolation) are never returned.
The Firestore SDK is synchronous, so calls run in a thread.
"""

import asyncio
from datetime import datetime
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

from app.domain.entities import Comparison, ConceptOccurrence, Policy

OCCURRENCES = "concept_occurrences"
_OWNERSHIP_FIELDS = ("owner_id", "expires_at")


def _is_owned(data: dict[str, Any] | None) -> bool:
    return bool(data and data.get("owner_id") and data.get("expires_at"))


def _owned_by(owner_id: str) -> FieldFilter:
    return FieldFilter("owner_id", "==", owner_id)


def _expired_before(before: datetime) -> FieldFilter:
    return FieldFilter("expires_at", "<", before)


class FirestorePolicyRepository:
    def __init__(self, client: Any) -> None:
        self._collection = client.collection("policies")

    async def save(self, policy: Policy) -> None:
        await asyncio.to_thread(self._save, policy)

    def _save(self, policy: Policy) -> None:
        data = policy.model_dump(mode="json", exclude={"occurrences"})
        data["expires_at"] = policy.expires_at
        reference = self._collection.document(policy.id)
        reference.set(data)
        occurrences = reference.collection(OCCURRENCES)
        existing = {snapshot.id for snapshot in occurrences.list_documents()}
        current = {occurrence.concept_id for occurrence in policy.occurrences}
        for occurrence in policy.occurrences:
            occurrences.document(occurrence.concept_id).set(
                {
                    **occurrence.model_dump(mode="json"),
                    "owner_id": policy.owner_id,
                    "expires_at": policy.expires_at,
                }
            )
        for stale in existing - current:
            occurrences.document(stale).delete()

    async def get(self, policy_id: str) -> Policy | None:
        return await asyncio.to_thread(self._get, policy_id)

    def _get(self, policy_id: str) -> Policy | None:
        reference = self._collection.document(policy_id)
        snapshot = reference.get()
        data = snapshot.to_dict() if snapshot.exists else None
        if not _is_owned(data):
            return None
        occurrences = [
            ConceptOccurrence.model_validate(
                {k: v for k, v in item.to_dict().items() if k not in _OWNERSHIP_FIELDS}
            )
            for item in reference.collection(OCCURRENCES).stream()
        ]
        return Policy.model_validate({**(data or {}), "occurrences": occurrences})

    async def list_recent(self, owner_id: str, limit: int) -> list[Policy]:
        def run() -> list[Policy]:
            query = (
                self._collection.where(filter=_owned_by(owner_id))
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
            )
            return self._load_all(snapshot.id for snapshot in query.stream())

        return await asyncio.to_thread(run)

    async def delete(self, policy_id: str) -> None:
        await asyncio.to_thread(self._delete, policy_id)

    def _delete(self, policy_id: str) -> None:
        reference = self._collection.document(policy_id)
        # Firestore does not delete subcollections with the parent document.
        for occurrence in reference.collection(OCCURRENCES).list_documents():
            occurrence.delete()
        reference.delete()

    async def delete_all_for_owner(self, owner_id: str) -> None:
        def run() -> None:
            for snapshot in self._collection.where(filter=_owned_by(owner_id)).stream():
                self._delete(snapshot.id)

        await asyncio.to_thread(run)

    async def list_expired(self, before: datetime, limit: int) -> list[Policy]:
        def run() -> list[Policy]:
            query = self._collection.where(filter=_expired_before(before)).limit(limit)
            return self._load_all(snapshot.id for snapshot in query.stream())

        return await asyncio.to_thread(run)

    def _load_all(self, policy_ids: Any) -> list[Policy]:
        policies: list[Policy] = []
        for policy_id in policy_ids:
            policy = self._get(policy_id)
            if policy:
                policies.append(policy)
        return policies


class FirestoreComparisonRepository:
    def __init__(self, client: Any) -> None:
        self._collection = client.collection("comparisons")

    async def save(self, comparison: Comparison) -> None:
        data = comparison.model_dump(mode="json")
        data["expires_at"] = comparison.expires_at
        await asyncio.to_thread(self._collection.document(comparison.id).set, data)

    async def get(self, comparison_id: str) -> Comparison | None:
        snapshot = await asyncio.to_thread(self._collection.document(comparison_id).get)
        data = snapshot.to_dict() if snapshot.exists else None
        return Comparison.model_validate(data) if _is_owned(data) else None

    async def list_recent(self, owner_id: str, limit: int) -> list[Comparison]:
        def run() -> list[Comparison]:
            query = (
                self._collection.where(filter=_owned_by(owner_id))
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
            )
            return [Comparison.model_validate(item.to_dict()) for item in query.stream()]

        return await asyncio.to_thread(run)

    async def count_active(self, owner_id: str, now: datetime) -> int:
        def run() -> int:
            query = self._collection.where(filter=_owned_by(owner_id)).select(["expires_at"])
            return sum(
                1
                for item in query.stream()
                if (expires_at := item.to_dict().get("expires_at")) and expires_at > now
            )

        return await asyncio.to_thread(run)

    async def delete(self, comparison_id: str) -> None:
        await asyncio.to_thread(self._collection.document(comparison_id).delete)

    async def delete_all_for_owner(self, owner_id: str) -> None:
        def run() -> None:
            for snapshot in self._collection.where(filter=_owned_by(owner_id)).stream():
                snapshot.reference.delete()

        await asyncio.to_thread(run)

    async def list_expired(self, before: datetime, limit: int) -> list[Comparison]:
        def run() -> list[Comparison]:
            query = self._collection.where(filter=_expired_before(before)).limit(limit)
            return [
                Comparison.model_validate(data)
                for item in query.stream()
                if _is_owned(data := item.to_dict())
            ]

        return await asyncio.to_thread(run)
