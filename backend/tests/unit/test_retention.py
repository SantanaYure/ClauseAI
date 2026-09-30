"""Retention (LGPD): expired data disappears for the owner at once and is swept later."""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from app.application.use_cases import RetentionSweeper
from app.domain.entities import Comparison, Policy, PolicyDocument, PolicyRef, utc_now
from app.domain.value_objects import DocumentType, FileKind, PolicyStatus, RiskProfile
from app.infrastructure.persistence import InMemoryComparisonRepository, InMemoryPolicyRepository
from app.infrastructure.scheduling import PeriodicJob
from app.infrastructure.storage import LocalBlobStorage
from fastapi.testclient import TestClient

from tests.fakes import PDF_BYTES, auth_headers, build_test_app


def _policy(policy_id: str, owner: str, expires_in: timedelta) -> Policy:
    key = f"owners/{owner}/policies/{policy_id}/{policy_id}_doc_1.pdf"
    return Policy(
        id=policy_id,
        owner_id=owner,
        expires_at=utc_now() + expires_in,
        insurer="X",
        name="Y",
        status=PolicyStatus.READY,
        correlation_id="c",
        documents=[
            PolicyDocument(
                id=f"{policy_id}_doc_1",
                policy_id=policy_id,
                filename="a.pdf",
                type=DocumentType.POLICY,
                content_type="application/pdf",
                file_kind=FileKind.SEARCHABLE_PDF,
                size_bytes=1,
                checksum_sha256="c",
                storage_key=key,
            )
        ],
    )


def _comparison(comparison_id: str, owner: str, expires_in: timedelta) -> Comparison:
    ref = PolicyRef(id="p", insurer="X", name="Y")
    return Comparison(
        id=comparison_id,
        owner_id=owner,
        expires_at=utc_now() + expires_in,
        knowledge_base_version="1",
        selected_profile=RiskProfile.BASE,
        policy_a=ref,
        policy_b=ref,
        correlation_id="c",
    )


async def test_sweeper_deletes_expired_documents_occurrences_and_files(tmp_path: Path) -> None:
    policies, comparisons = InMemoryPolicyRepository(), InMemoryComparisonRepository()
    storage = LocalBlobStorage(tmp_path)
    old, fresh = (
        _policy("pol_old", "alice", -timedelta(minutes=1)),
        _policy("pol_new", "alice", timedelta(hours=23)),
    )
    for policy in (old, fresh):
        await policies.save(policy)
        await storage.put(policy.documents[0].storage_key, b"%PDF", "application/pdf")
    await comparisons.save(_comparison("cmp_old", "alice", -timedelta(seconds=1)))
    await comparisons.save(_comparison("cmp_new", "bob", timedelta(hours=1)))

    result = await RetentionSweeper(policies, comparisons, storage, batch_size=1).sweep()

    assert (result.policies, result.comparisons) == (1, 1)
    assert await policies.get("pol_old") is None
    assert await policies.get("pol_new") is not None
    assert await comparisons.get("cmp_old") is None
    assert await comparisons.get("cmp_new") is not None
    assert not (tmp_path / "owners/alice/policies/pol_old").exists()
    assert (tmp_path / fresh.documents[0].storage_key).exists()


async def test_second_sweep_finds_nothing(tmp_path: Path) -> None:
    policies, comparisons = InMemoryPolicyRepository(), InMemoryComparisonRepository()
    sweeper = RetentionSweeper(policies, comparisons, LocalBlobStorage(tmp_path))
    await policies.save(_policy("pol_old", "alice", -timedelta(hours=1)))

    assert (await sweeper.sweep()).policies == 1
    assert (await sweeper.sweep()).policies == 0


def test_expired_items_are_hidden_before_the_sweep(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)
    runtime = app.state.runtime
    with TestClient(app, headers=auth_headers("alice")) as client:
        asyncio.run(runtime.policies.save(_policy("pol_old", "alice", -timedelta(seconds=1))))
        asyncio.run(
            runtime.comparisons.save(_comparison("cmp_old", "alice", -timedelta(seconds=1)))
        )

        assert client.get("/api/v1/policies/pol_old").status_code == 404
        assert client.get("/api/v1/policies").json()["items"] == []
        assert client.get("/api/v1/comparisons/cmp_old").status_code == 404
        assert client.get("/api/v1/comparisons").json()["items"] == []
        assert client.get("/api/v1/me/data/summary").json() == {
            "policies": 0,
            "documents": 0,
            "comparisons": 0,
        }


def test_uploaded_policy_expires_24_hours_after_upload(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path), headers=auth_headers()) as client:
        before = utc_now()
        created = client.post(
            "/api/v1/policies",
            data={"document_types": ["POLICY"]},
            files=[("files", ("a.pdf", PDF_BYTES, "application/pdf"))],
        ).json()
        after = utc_now()

    expires_at = datetime.fromisoformat(created["expires_at"])
    assert before + timedelta(hours=24) <= expires_at <= after + timedelta(hours=24)


async def test_periodic_job_runs_at_start_and_survives_failures() -> None:
    runs: list[int] = []

    async def flaky() -> None:
        runs.append(1)
        if len(runs) == 1:
            raise RuntimeError("falha transitória")

    job = PeriodicJob("teste", flaky, interval_seconds=0.01)
    await job.start()
    await asyncio.sleep(0.1)
    await job.stop()

    assert len(runs) >= 2


class _FailingComparisons(InMemoryComparisonRepository):
    """Deletion always fails for the given ids, like a stuck document."""

    def __init__(self, stuck: set[str]) -> None:
        super().__init__()
        self._stuck = stuck

    async def delete(self, comparison_id: str) -> None:
        if comparison_id in self._stuck:
            raise RuntimeError("falha permanente")
        await super().delete(comparison_id)


async def test_sweep_advances_past_items_that_keep_failing(tmp_path: Path) -> None:
    stuck = {"cmp_0", "cmp_1"}
    comparisons = _FailingComparisons(stuck)
    for index in range(7):
        await comparisons.save(_comparison(f"cmp_{index}", "alice", -timedelta(minutes=1)))
    sweeper = RetentionSweeper(
        InMemoryPolicyRepository(), comparisons, LocalBlobStorage(tmp_path), batch_size=2
    )

    result = await sweeper.sweep()

    assert result.comparisons == 5
    remaining = await comparisons.list_expired(utc_now(), 10)
    assert {c.id for c in remaining} == stuck


async def test_failed_deletions_are_logged_without_owner(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    comparisons = _FailingComparisons({"cmp_0"})
    await comparisons.save(_comparison("cmp_0", "alice@example.com", -timedelta(minutes=1)))
    sweeper = RetentionSweeper(InMemoryPolicyRepository(), comparisons, LocalBlobStorage(tmp_path))

    with caplog.at_level(logging.INFO):
        assert (await sweeper.sweep()).comparisons == 0

    assert "could not be deleted" in caplog.text
    assert "alice" not in caplog.text


async def test_periodic_job_start_does_not_wait_for_the_first_run() -> None:
    release = asyncio.Event()

    async def slow_sweep() -> None:
        await release.wait()

    job = PeriodicJob("teste", slow_sweep, interval_seconds=60)
    await asyncio.wait_for(job.start(), timeout=0.5)
    release.set()
    await job.stop()
