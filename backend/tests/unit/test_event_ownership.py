"""Events carry the owner: a handler never works on someone else's entity (SPEC-020)."""

from pathlib import Path

import pytest
from app.application.use_cases import COMPARISON_REQUESTED, POLICY_UPLOADED
from app.domain.entities import Comparison, Policy, PolicyRef, utc_now
from app.domain.interfaces.events import Event
from app.domain.value_objects import ComparisonStatus, PolicyStatus, RiskProfile

from tests.fakes import RETENTION, build_test_app


def _policy(policy_id: str, owner_id: str) -> Policy:
    now = utc_now()
    return Policy(
        id=policy_id,
        owner_id=owner_id,
        expires_at=now + RETENTION,
        insurer="Seguradora",
        name="Apólice",
        correlation_id="c1",
    )


@pytest.mark.parametrize("payload_owner", ["mallory", None, ""])
async def test_policy_uploaded_with_another_owner_is_discarded(
    tmp_path: Path, payload_owner: str | None
) -> None:
    app = build_test_app(tmp_path)
    runtime = app.state.runtime
    await runtime.policies.save(_policy("pol_1", "alice"))
    payload: dict[str, object] = {"policy_id": "pol_1"}
    if payload_owner is not None:
        payload["owner_id"] = payload_owner

    await app.state.services.policies.handle_policy_uploaded(
        Event.create(POLICY_UPLOADED, "c1", payload)
    )

    stored = await runtime.policies.get("pol_1")
    assert stored is not None
    assert stored.owner_id == "alice"
    assert stored.status == PolicyStatus.PROCESSING


async def test_policy_uploaded_for_a_deleted_policy_does_not_recreate_it(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)

    await app.state.services.policies.handle_policy_uploaded(
        Event.create(POLICY_UPLOADED, "c1", {"policy_id": "pol_gone", "owner_id": "alice"})
    )

    assert await app.state.runtime.policies.get("pol_gone") is None


async def test_comparison_requested_with_another_owner_is_discarded(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)
    runtime = app.state.runtime
    comparison = Comparison(
        id="cmp_1",
        owner_id="alice",
        expires_at=utc_now() + RETENTION,
        knowledge_base_version="1",
        selected_profile=RiskProfile.BASE,
        policy_a=PolicyRef(id="pol_a", insurer="A", name="A"),
        policy_b=PolicyRef(id="pol_b", insurer="B", name="B"),
        correlation_id="c1",
    )
    await runtime.comparisons.save(comparison)

    await app.state.services.comparisons.handle_comparison_requested(
        Event.create(COMPARISON_REQUESTED, "c1", {"comparison_id": "cmp_1", "owner_id": "bob"})
    )

    stored = await runtime.comparisons.get("cmp_1")
    assert stored is not None
    assert stored.status == ComparisonStatus.REQUESTED
