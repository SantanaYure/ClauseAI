"""LGPD: the owner sees what is stored and can erase all of it (and only it)."""

import asyncio
from pathlib import Path

from app.application.commands import CreatePolicyCommand, UploadedFile
from app.domain.value_objects import DocumentType
from fastapi.testclient import TestClient

from tests.fakes import PDF_BYTES, FakeExtractor, auth_headers, build_test_app
from tests.integration.test_owner_isolation import ALICE, BOB, _compare, _upload


def _upload_two_documents(client: TestClient) -> None:
    response = client.post(
        "/api/v1/policies",
        headers=ALICE,
        data={"document_types": ["POLICY", "GENERAL_CONDITIONS"]},
        files=[
            ("files", ("a.pdf", PDF_BYTES, "application/pdf")),
            ("files", ("b.pdf", PDF_BYTES, "application/pdf")),
        ],
    )
    assert response.status_code == 202


def test_summary_counts_only_the_callers_data(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path)) as client:
        empty = client.get("/api/v1/me/data/summary", headers=ALICE)
        assert empty.status_code == 200
        assert empty.json() == {"policies": 0, "documents": 0, "comparisons": 0}

        first, second = _upload(client, ALICE), _upload(client, ALICE)
        _upload_two_documents(client)
        _compare(client, ALICE, first, second)
        _upload(client, BOB)

        assert client.get("/api/v1/me/data/summary", headers=ALICE).json() == {
            "policies": 3,
            "documents": 4,
            "comparisons": 1,
        }
        assert client.get("/api/v1/me/data/summary", headers=BOB).json() == {
            "policies": 1,
            "documents": 1,
            "comparisons": 0,
        }


def test_erase_removes_everything_of_the_owner_and_nothing_else(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)
    runtime = app.state.runtime
    with TestClient(app) as client:
        first, second = _upload(client, ALICE), _upload(client, ALICE)
        comparison_id = _compare(client, ALICE, first, second)
        bob_policy = _upload(client, BOB)
        assert list((tmp_path / "owners" / "alice").rglob("*.pdf"))

        response = client.delete("/api/v1/me/data", headers=ALICE)

        assert response.status_code == 204
        assert client.get("/api/v1/policies", headers=ALICE).json()["items"] == []
        assert client.get("/api/v1/comparisons", headers=ALICE).json()["items"] == []
        assert client.get(f"/api/v1/comparisons/{comparison_id}", headers=ALICE).status_code == 404
        assert not (tmp_path / "owners" / "alice").exists()
        assert runtime.accounts.removed == ["alice"]
        # Bob is untouched.
        assert client.get(f"/api/v1/policies/{bob_policy}", headers=BOB).status_code == 200
        assert list((tmp_path / "owners" / "bob").rglob("*.pdf"))

        again = client.delete("/api/v1/me/data", headers=ALICE)
        assert again.status_code == 204  # idempotent
        assert client.get("/api/v1/me/data/summary", headers=ALICE).json() == {
            "policies": 0,
            "documents": 0,
            "comparisons": 0,
        }


async def test_erase_cancels_processing_and_the_worker_does_not_write_back(
    tmp_path: Path,
) -> None:
    started = asyncio.Event()

    class SlowExtractor(FakeExtractor):
        async def extract(self, content, knowledge_base):  # type: ignore[no-untyped-def]
            started.set()
            await asyncio.sleep(30)
            return await super().extract(content, knowledge_base)

    app = build_test_app(tmp_path, SlowExtractor())
    services = app.state.services
    runtime = app.state.runtime
    async with app.router.lifespan_context(app):
        policy = await services.policies.create_policy(
            CreatePolicyCommand(
                owner_id="alice",
                insurer=None,
                name=None,
                correlation_id="c1",
                files=[UploadedFile("a.pdf", "application/pdf", PDF_BYTES, DocumentType.POLICY)],
            )
        )
        await asyncio.wait_for(started.wait(), 5)

        await services.owner_data.erase("alice")
        await asyncio.sleep(0.2)

        assert await runtime.policies.get(policy.id) is None
        assert await runtime.policies.list_recent("alice", 10) == []


def test_erase_requires_a_token(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path)) as client:
        assert client.delete("/api/v1/me/data").status_code == 401
        assert client.delete("/api/v1/me/data", headers=auth_headers("x")).status_code == 204
