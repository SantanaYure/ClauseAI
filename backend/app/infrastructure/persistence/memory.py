"""Process-local repositories for automated tests and runs without Firebase.

Data lives only while the process runs; nothing is pre-loaded.
"""

from datetime import datetime

from app.domain.entities import Comparison, Policy


class InMemoryPolicyRepository:
    def __init__(self) -> None:
        self._items: dict[str, Policy] = {}

    async def save(self, policy: Policy) -> None:
        self._items[policy.id] = policy.model_copy(deep=True)

    async def get(self, policy_id: str) -> Policy | None:
        policy = self._items.get(policy_id)
        return policy.model_copy(deep=True) if policy else None

    async def list_recent(self, owner_id: str, limit: int) -> list[Policy]:
        owned = [p for p in self._items.values() if p.owner_id == owner_id]
        ordered = sorted(owned, key=lambda p: p.created_at, reverse=True)
        return [policy.model_copy(deep=True) for policy in ordered[:limit]]

    async def delete(self, policy_id: str) -> None:
        self._items.pop(policy_id, None)

    async def delete_all_for_owner(self, owner_id: str) -> None:
        for policy_id in [p.id for p in self._items.values() if p.owner_id == owner_id]:
            del self._items[policy_id]

    async def list_expired(self, before: datetime, limit: int) -> list[Policy]:
        expired = [p for p in self._items.values() if p.expires_at < before]
        return [policy.model_copy(deep=True) for policy in expired[:limit]]


class InMemoryComparisonRepository:
    def __init__(self) -> None:
        self._items: dict[str, Comparison] = {}

    async def save(self, comparison: Comparison) -> None:
        self._items[comparison.id] = comparison.model_copy(deep=True)

    async def get(self, comparison_id: str) -> Comparison | None:
        comparison = self._items.get(comparison_id)
        return comparison.model_copy(deep=True) if comparison else None

    async def list_recent(self, owner_id: str, limit: int) -> list[Comparison]:
        owned = [c for c in self._items.values() if c.owner_id == owner_id]
        ordered = sorted(owned, key=lambda c: c.created_at, reverse=True)
        return [comparison.model_copy(deep=True) for comparison in ordered[:limit]]

    async def count_active(self, owner_id: str, now: datetime) -> int:
        return sum(
            1 for c in self._items.values() if c.owner_id == owner_id and not c.is_expired(now)
        )

    async def delete(self, comparison_id: str) -> None:
        self._items.pop(comparison_id, None)

    async def delete_all_for_owner(self, owner_id: str) -> None:
        for comparison_id in [c.id for c in self._items.values() if c.owner_id == owner_id]:
            del self._items[comparison_id]

    async def list_expired(self, before: datetime, limit: int) -> list[Comparison]:
        expired = [c for c in self._items.values() if c.expires_at < before]
        return [comparison.model_copy(deep=True) for comparison in expired[:limit]]
