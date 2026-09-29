"""Process-local repositories for automated tests and runs without Firebase.

Data lives only while the process runs; nothing is pre-loaded.
"""

from app.domain.entities import Comparison, Policy


class InMemoryPolicyRepository:
    def __init__(self) -> None:
        self._items: dict[str, Policy] = {}

    async def save(self, policy: Policy) -> None:
        self._items[policy.id] = policy.model_copy(deep=True)

    async def get(self, policy_id: str) -> Policy | None:
        policy = self._items.get(policy_id)
        return policy.model_copy(deep=True) if policy else None

    async def list_recent(self, limit: int) -> list[Policy]:
        ordered = sorted(self._items.values(), key=lambda p: p.created_at, reverse=True)
        return [policy.model_copy(deep=True) for policy in ordered[:limit]]

    async def delete(self, policy_id: str) -> None:
        self._items.pop(policy_id, None)


class InMemoryComparisonRepository:
    def __init__(self) -> None:
        self._items: dict[str, Comparison] = {}

    async def save(self, comparison: Comparison) -> None:
        self._items[comparison.id] = comparison.model_copy(deep=True)

    async def get(self, comparison_id: str) -> Comparison | None:
        comparison = self._items.get(comparison_id)
        return comparison.model_copy(deep=True) if comparison else None

    async def list_recent(self, limit: int) -> list[Comparison]:
        ordered = sorted(self._items.values(), key=lambda c: c.created_at, reverse=True)
        return [comparison.model_copy(deep=True) for comparison in ordered[:limit]]
