"""Retention sweep (LGPD): delete everything past its `expires_at`.

This sweep is the only deletion mechanism: the Firestore TTL policy is not active (the
project has no billing). It runs at startup and every RETENTION_SWEEP_MINUTES; between
runs, reads already hide expired items from their owner.
"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.application.storage_keys import policy_prefix
from app.domain.entities import Comparison, Policy, utc_now
from app.domain.interfaces.ports import BlobStorage, ComparisonRepository, PolicyRepository
from app.shared.logging import error_fields, get_logger, log_context

logger = get_logger(__name__)

SWEEP_BATCH_SIZE = 100
# Bounds one sweep; whatever is left (or keeps failing) is retried by the next sweep.
MAX_BATCHES = 20


class _Expirable(Protocol):
    @property
    def id(self) -> str: ...


@dataclass(frozen=True, slots=True)
class SweepResult:
    policies: int
    comparisons: int


class RetentionSweeper:
    def __init__(
        self,
        policies: PolicyRepository,
        comparisons: ComparisonRepository,
        storage: BlobStorage,
        batch_size: int = SWEEP_BATCH_SIZE,
    ) -> None:
        self._policies = policies
        self._comparisons = comparisons
        self._storage = storage
        self._batch_size = batch_size

    async def sweep(self, now: datetime | None = None) -> SweepResult:
        moment = now or utc_now()
        comparisons = await self._sweep(
            "comparison",
            lambda limit: self._comparisons.list_expired(moment, limit),
            self._delete_comparison,
        )
        policies = await self._sweep(
            "policy",
            lambda limit: self._policies.list_expired(moment, limit),
            self._delete_policy,
        )
        if policies or comparisons:
            with log_context(policies=str(policies), comparisons=str(comparisons)):
                logger.info("Expired data deleted")
        return SweepResult(policies=policies, comparisons=comparisons)

    async def _delete_policy(self, policy: Policy) -> None:
        await self._storage.delete_prefix(policy_prefix(policy.owner_id, policy.id))
        await self._policies.delete(policy.id)

    async def _delete_comparison(self, comparison: Comparison) -> None:
        await self._comparisons.delete(comparison.id)

    async def _sweep[T: _Expirable](
        self,
        kind: str,
        list_expired: Callable[[int], Awaitable[Sequence[T]]],
        delete: Callable[[T], Awaitable[None]],
    ) -> int:
        """Delete in batches; items that fail are skipped so the sweep keeps advancing.

        The listing has no cursor, so each batch asks for as many extra items as have
        already failed in this run and ignores them; a batch without new items ends it.
        """

        deleted = 0
        failed: set[str] = set()
        for _ in range(MAX_BATCHES):
            listed = await list_expired(self._batch_size + len(failed))
            batch = [item for item in listed if item.id not in failed]
            for item in batch:
                try:
                    await delete(item)
                    deleted += 1
                except Exception as exc:
                    failed.add(item.id)
                    # Ids are random and carry no personal data; the owner is not logged.
                    with log_context(kind=kind, item_id=item.id, **error_fields(exc)):
                        logger.error("Expired item could not be deleted")
            if len(batch) < self._batch_size:
                break
        if failed:
            with log_context(kind=kind, failed=str(len(failed))):
                logger.warning("Retention sweep left items for the next run")
        return deleted
