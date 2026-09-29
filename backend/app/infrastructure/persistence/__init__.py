"""Persistence adapters."""

from app.infrastructure.persistence.firestore import (
    FirestoreComparisonRepository,
    FirestorePolicyRepository,
)
from app.infrastructure.persistence.memory import (
    InMemoryComparisonRepository,
    InMemoryPolicyRepository,
)

__all__ = [
    "FirestoreComparisonRepository",
    "FirestorePolicyRepository",
    "InMemoryComparisonRepository",
    "InMemoryPolicyRepository",
]
