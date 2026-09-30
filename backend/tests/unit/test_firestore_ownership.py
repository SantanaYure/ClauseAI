"""Firestore adapters: owner filter, legacy records hidden, timestamps for TTL."""

from datetime import datetime, timedelta

from app.domain.entities import utc_now
from app.infrastructure.persistence import (
    FirestoreComparisonRepository,
    FirestorePolicyRepository,
)

from tests.fakes import occurrence
from tests.firestore_fake import FakeFirestoreClient
from tests.unit.test_retention import _comparison, _policy


async def test_policies_are_listed_only_for_their_owner() -> None:
    client = FakeFirestoreClient()
    repository = FirestorePolicyRepository(client)
    alice = _policy("pol_a", "alice", timedelta(hours=1))
    alice.occurrences = [occurrence("DO-002", "CONTRACTED")]  # type: ignore[arg-type]
    await repository.save(alice)
    await repository.save(_policy("pol_b", "bob", timedelta(hours=1)))

    listed = await repository.list_recent("alice", 10)

    assert [p.id for p in listed] == ["pol_a"]
    assert listed[0].occurrences[0].concept_id == "DO-002"
    stored = client.store["policies/pol_a"]
    assert isinstance(stored["expires_at"], datetime)  # native timestamp for the TTL policy
    child = client.store["policies/pol_a/concept_occurrences/DO-002"]
    assert child["owner_id"] == "alice" and isinstance(child["expires_at"], datetime)


async def test_legacy_documents_without_owner_are_invisible() -> None:
    client = FakeFirestoreClient()
    client.store["policies/pol_legacy"] = {"id": "pol_legacy", "insurer": "X", "created_at": "z"}
    client.store["comparisons/cmp_legacy"] = {"id": "cmp_legacy", "created_at": "z"}

    assert await FirestorePolicyRepository(client).get("pol_legacy") is None
    assert await FirestoreComparisonRepository(client).get("cmp_legacy") is None
    assert await FirestorePolicyRepository(client).list_recent("alice", 10) == []


async def test_delete_all_for_owner_and_list_expired() -> None:
    client = FakeFirestoreClient()
    policies = FirestorePolicyRepository(client)
    comparisons = FirestoreComparisonRepository(client)
    expired = _policy("pol_old", "alice", -timedelta(minutes=1))
    expired.occurrences = [occurrence("DO-002", "CONTRACTED")]  # type: ignore[arg-type]
    await policies.save(expired)
    await policies.save(_policy("pol_new", "bob", timedelta(hours=1)))
    await comparisons.save(_comparison("cmp_a", "alice", timedelta(hours=1)))
    await comparisons.save(_comparison("cmp_b", "bob", -timedelta(hours=1)))

    assert [p.id for p in await policies.list_expired(utc_now(), 10)] == ["pol_old"]
    assert [c.id for c in await comparisons.list_expired(utc_now(), 10)] == ["cmp_b"]
    assert await comparisons.count_active("alice", utc_now()) == 1
    assert await comparisons.count_active("bob", utc_now()) == 0

    await policies.delete_all_for_owner("alice")
    await comparisons.delete_all_for_owner("alice")

    assert sorted(client.store) == ["comparisons/cmp_b", "policies/pol_new"]
