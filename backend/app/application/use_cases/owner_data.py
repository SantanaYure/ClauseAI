"""The owner's rights over their data (LGPD): see what is stored and erase all of it."""

from dataclasses import dataclass

from app.application.storage_keys import owner_prefix
from app.application.use_cases.comparisons import ComparisonService
from app.application.use_cases.policies import PolicyService
from app.domain.interfaces.ports import (
    AccountRemover,
    BlobStorage,
    ComparisonRepository,
    PolicyRepository,
)
from app.shared.logging import get_logger, log_context, owner_ref

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OwnerDataSummary:
    policies: int
    documents: int
    comparisons: int


class OwnerDataService:
    def __init__(
        self,
        policy_service: PolicyService,
        comparison_service: ComparisonService,
        policies: PolicyRepository,
        comparisons: ComparisonRepository,
        storage: BlobStorage,
        accounts: AccountRemover,
    ) -> None:
        self._policy_service = policy_service
        self._comparison_service = comparison_service
        self._policies = policies
        self._comparisons = comparisons
        self._storage = storage
        self._accounts = accounts

    async def summary(self, owner_id: str) -> OwnerDataSummary:
        """What the owner currently sees (expired items are already gone for them)."""

        policies = await self._policy_service.list_policies(owner_id)
        return OwnerDataSummary(
            policies=len(policies),
            documents=sum(len(policy.documents) for policy in policies),
            comparisons=await self._comparison_service.count_active(owner_id),
        )

    async def erase(self, owner_id: str) -> None:
        """Erase everything the owner has, then the anonymous account itself.

        Idempotent: erasing an owner with nothing stored succeeds. Running jobs are
        cancelled first so they do not write the data back.
        """

        await self._policy_service.cancel_processing_for(owner_id)
        await self._comparisons.delete_all_for_owner(owner_id)
        await self._policies.delete_all_for_owner(owner_id)
        await self._storage.delete_prefix(owner_prefix(owner_id))
        await self._accounts.remove(owner_id)
        with log_context(owner_ref=owner_ref(owner_id)):
            logger.info("Owner data erased")
