import time
from pathlib import Path

from app.domain.value_objects import ContractStatus
from fastapi.testclient import TestClient

from tests.fakes import PDF_BYTES, FakeExtractor, auth_headers, build_test_app, make_docx


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
    with TestClient(app, headers=auth_headers()) as client:
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
    with TestClient(build_test_app(tmp_path), headers=auth_headers()) as client:
        concepts = client.get("/api/v1/concepts").json()["items"]
        assert len(concepts) == 44
        assert client.get("/api/v1/concepts/DO-036").json()["weight"] == 10


def test_validation_errors_use_the_error_envelope(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path), headers=auth_headers()) as client:
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


def test_delete_policy_removes_record_and_files(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path), headers=auth_headers()) as client:
        policy_id = upload(client, ["POLICY", "GENERAL_CONDITIONS"])
        wait_for(client, f"/api/v1/policies/{policy_id}", {"READY", "ATTENTION", "FAILED"})
        assert list(tmp_path.rglob("*.pdf"))

        deleted = client.delete(f"/api/v1/policies/{policy_id}")

        assert deleted.status_code == 204
        assert client.get(f"/api/v1/policies/{policy_id}").status_code == 404
        assert client.get("/api/v1/policies").json()["items"] == []
        assert not list(tmp_path.rglob("*.pdf"))

        again = client.delete(f"/api/v1/policies/{policy_id}")
        assert again.status_code == 404
        assert again.json()["error"]["code"] == "POLICY_NOT_FOUND"


def test_comparisons_stay_in_history_after_policy_deletion(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path), headers=auth_headers()) as client:
        policy_a = upload(client, ["POLICY"])
        policy_b = upload(client, ["POLICY"])
        for policy_id in (policy_a, policy_b):
            wait_for(client, f"/api/v1/policies/{policy_id}", {"READY", "ATTENTION", "FAILED"})
        created = client.post(
            "/api/v1/comparisons", json={"policy_a_id": policy_a, "policy_b_id": policy_b}
        ).json()
        url = f"/api/v1/comparisons/{created['comparison_id']}"
        wait_for(client, url, {"COMPLETED", "PARTIAL", "FAILED"})

        assert client.delete(f"/api/v1/policies/{policy_a}").status_code == 204

        comparison = client.get(url).json()
        assert comparison["status"] == "COMPLETED"
        assert len(comparison["items"]) == 31


def test_cancel_policy_endpoint(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path), headers=auth_headers()) as client:
        policy_id = upload(client, ["POLICY"])
        # Wait until extraction finishes
        wait_for(client, f"/api/v1/policies/{policy_id}", {"READY", "ATTENTION", "FAILED"})

        # Trying to cancel a completed policy returns 400 Bad Request
        response = client.post(f"/api/v1/policies/{policy_id}/cancel")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "POLICY_NOT_PROCESSING"


def _upload_docx(client: TestClient) -> str:
    response = client.post(
        "/api/v1/policies",
        data={"document_types": ["POLICY"]},
        files=[("files", ("apolice.docx", make_docx(), "application/octet-stream"))],
    )
    assert response.status_code == 202, response.text
    return str(response.json()["policy_id"])


def test_comparison_works_for_pdf_docx_and_mixed_policies(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)
    with TestClient(app, headers=auth_headers()) as client:
        pdf_a, pdf_b = upload(client, ["POLICY"]), upload(client, ["POLICY"])
        docx_a, docx_b = _upload_docx(client), _upload_docx(client)
        done = {"READY", "ATTENTION", "FAILED"}
        for policy_id in (pdf_a, pdf_b, docx_a, docx_b):
            wait_for(client, f"/api/v1/policies/{policy_id}", done)
        detail = client.get(f"/api/v1/policies/{docx_a}").json()
        assert detail["documents"][0]["file_kind"] == "DOCX"
        assert detail["documents"][0]["status"] == "COMPLETED"

        for first, second in ((pdf_a, pdf_b), (docx_a, docx_b), (pdf_a, docx_a)):
            created = client.post(
                "/api/v1/comparisons",
                json={"policy_a_id": first, "policy_b_id": second, "selected_profile": "FINANCIAL"},
            )
            assert created.status_code == 202, created.text
            result = wait_for(
                client,
                f"/api/v1/comparisons/{created.json()['comparison_id']}",
                {"COMPLETED", "PARTIAL", "FAILED"},
            )
            assert result["status"] in {"COMPLETED", "PARTIAL"}


def test_upload_rejects_xlsx_disguised_as_docx(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)
    with TestClient(app, headers=auth_headers()) as client:
        response = client.post(
            "/api/v1/policies",
            data={"document_types": ["POLICY"]},
            files=[
                ("files", ("planilha.docx", b"PK\x03\x04 planilha", "application/vnd.ms-excel"))
            ],
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "DOCX_CORRUPTED"
