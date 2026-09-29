import time
from pathlib import Path

from app.domain.value_objects import ContractStatus
from fastapi.testclient import TestClient

from tests.fakes import PDF_BYTES, FakeExtractor, build_test_app


def wait_for(client: TestClient, url: str, done: set[str], timeout: float = 10) -> dict:  # type: ignore[type-arg]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get(url).json()
        if body["status"] in done:
            return body  # type: ignore[no-any-return]
        time.sleep(0.05)
    raise AssertionError(f"{url} did not finish")


def upload(client: TestClient, types: list[str], insurer: str = "") -> str:
    response = client.post(
        "/api/v1/policies",
        data={"document_types": types, "insurer": insurer},
        files=[("files", (f"doc{i}.pdf", PDF_BYTES, "application/pdf")) for i in range(len(types))],
    )
    assert response.status_code == 202, response.text
    return str(response.json()["policy_id"])


def test_full_flow_from_upload_to_weighted_comparison(tmp_path: Path) -> None:
    app = build_test_app(tmp_path, FakeExtractor({"DO-040": ContractStatus.NOT_FOUND}))
    with TestClient(app) as client:
        policy_a = upload(client, ["POLICY", "GENERAL_CONDITIONS"], insurer="Seguradora Aurora")
        policy_b = upload(client, ["GENERAL_CONDITIONS"])

        detail_a = wait_for(
            client, f"/api/v1/policies/{policy_a}", {"READY", "ATTENTION", "FAILED"}
        )
        detail_b = wait_for(
            client, f"/api/v1/policies/{policy_b}", {"READY", "ATTENTION", "FAILED"}
        )
        assert detail_a["insurer"] == "Seguradora Aurora"
        assert detail_b["insurer"] == "Seguradora Teste"  # identified by the extractor
        assert all(d["status"] == "COMPLETED" for d in detail_a["documents"])
        # Only general conditions: nothing can be contracted.
        assert {o["contract_status"] for o in detail_b["occurrences"]} == {"NOT_PROVEN"}
        assert any("contratação não pode ser comprovada" in a for a in detail_b["alerts"])

        created = client.post(
            "/api/v1/comparisons",
            json={
                "policy_a_id": policy_a,
                "policy_b_id": policy_b,
                "selected_profile": "FINANCIAL",
            },
        )
        assert created.status_code == 202
        comparison_id = created.json()["comparison_id"]
        result = wait_for(
            client, f"/api/v1/comparisons/{comparison_id}", {"COMPLETED", "PARTIAL", "FAILED"}
        )
        assert result["status"] == "COMPLETED", result.get("failure")
        assert len(result["items"]) == 31
        assert result["summary"]["decision_mode"] == "CONDITIONED"
        base = next(p for p in result["profiles"] if p["profile"] == "BASE")
        assert base["a"]["max"] == 207
        assert base["b"]["completeness"] == 0
        assert any(check["id"] == "weights" and check["passed"] for check in result["quality_gate"])

        history = client.get("/api/v1/comparisons").json()["items"]
        assert history[0]["id"] == comparison_id
        assert history[0]["decision_mode"] == "CONDITIONED"

        answer = client.post("/api/v1/queries", json={"question": "A Aurora cobre multas?"}).json()
        assert answer["concept"]["id"] == "DO-015"
        assert [m["policy"]["id"] for m in answer["matches"]] == [policy_a]

        occurrences = client.get("/api/v1/concepts/DO-015/occurrences").json()["items"]
        assert {o["policy"]["id"] for o in occurrences} == {policy_a, policy_b}


def test_catalog_is_served(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path)) as client:
        concepts = client.get("/api/v1/concepts").json()["items"]
        assert len(concepts) == 44
        assert client.get("/api/v1/concepts/DO-036").json()["weight"] == 10


def test_validation_errors_use_the_error_envelope(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path)) as client:
        unsupported = client.post(
            "/api/v1/policies",
            data={"document_types": ["POLICY"]},
            files=[("files", ("planilha.xlsx", b"PK\x03\x04", "application/pdf"))],
        )
        assert unsupported.status_code == 415
        assert unsupported.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

        same = client.post(
            "/api/v1/comparisons", json={"policy_a_id": "pol_x", "policy_b_id": "pol_x"}
        )
        assert same.status_code == 400
        assert same.json()["error"]["code"] == "SAME_POLICY"

        missing = client.get("/api/v1/policies/pol_inexistente", headers={"X-Correlation-ID": "c1"})
        assert missing.status_code == 404
        assert missing.json()["error"] == {
            "code": "POLICY_NOT_FOUND",
            "message": "Apólice não encontrada.",
            "correlation_id": "c1",
            "details": None,
        }
