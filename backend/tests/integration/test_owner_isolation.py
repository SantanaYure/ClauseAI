"""Owner isolation (IDOR): another browser never sees, changes or compares my data."""

from pathlib import Path

from fastapi.testclient import TestClient

from tests.fakes import PDF_BYTES, auth_headers, build_test_app
from tests.integration.test_api_flow import wait_for

DONE = {"READY", "ATTENTION", "FAILED"}
COMPARISON_DONE = {"COMPLETED", "PARTIAL", "FAILED"}
ALICE = auth_headers("alice")
BOB = auth_headers("bob")


def _upload(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/policies",
        headers=headers,
        data={"document_types": ["POLICY"], "insurer": "Seguradora Aurora"},
        files=[("files", ("apolice.pdf", PDF_BYTES, "application/pdf"))],
    )
    assert response.status_code == 202, response.text
    policy_id = str(response.json()["policy_id"])
    client.headers.update(headers)
    wait_for(client, f"/api/v1/policies/{policy_id}", DONE)
    return policy_id


def _compare(client: TestClient, headers: dict[str, str], a: str, b: str) -> str:
    response = client.post(
        "/api/v1/comparisons", headers=headers, json={"policy_a_id": a, "policy_b_id": b}
    )
    assert response.status_code == 202, response.text
    comparison_id = str(response.json()["comparison_id"])
    client.headers.update(headers)
    wait_for(client, f"/api/v1/comparisons/{comparison_id}", COMPARISON_DONE)
    return comparison_id


def _error(response: object) -> dict[str, object]:
    body = response.json()["error"]  # type: ignore[attr-defined]
    body.pop("correlation_id")
    return body  # type: ignore[no-any-return]


def test_other_owner_gets_the_same_404_as_a_missing_policy(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path)) as client:
        policy_id = _upload(client, ALICE)
        missing = client.get("/api/v1/policies/pol_inexistente", headers=BOB)

        for method, url in (
            ("GET", f"/api/v1/policies/{policy_id}"),
            ("DELETE", f"/api/v1/policies/{policy_id}"),
            ("POST", f"/api/v1/policies/{policy_id}/cancel"),
        ):
            response = client.request(method, url, headers=BOB)
            assert response.status_code == 404, (method, url)
            assert _error(response) == _error(missing)

        assert client.get("/api/v1/policies", headers=BOB).json()["items"] == []
        # Bob's attempts changed nothing for Alice.
        assert client.get(f"/api/v1/policies/{policy_id}", headers=ALICE).status_code == 200


def test_comparisons_are_isolated_and_only_between_own_policies(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path)) as client:
        alice_a, alice_b = _upload(client, ALICE), _upload(client, ALICE)
        bob_policy = _upload(client, BOB)

        for headers, pair in (
            (BOB, (alice_a, alice_b)),
            (BOB, (bob_policy, alice_a)),
            (ALICE, (alice_a, bob_policy)),
        ):
            response = client.post(
                "/api/v1/comparisons",
                headers=headers,
                json={"policy_a_id": pair[0], "policy_b_id": pair[1]},
            )
            assert response.status_code == 404
            assert response.json()["error"]["code"] == "POLICY_NOT_FOUND"

        comparison_id = _compare(client, ALICE, alice_a, alice_b)
        stolen = client.get(f"/api/v1/comparisons/{comparison_id}", headers=BOB)
        missing = client.get("/api/v1/comparisons/cmp_inexistente", headers=BOB)
        assert stolen.status_code == missing.status_code == 404
        assert _error(stolen) == _error(missing)
        assert _error(stolen)["code"] == "COMPARISON_NOT_FOUND"
        assert client.get("/api/v1/comparisons", headers=BOB).json()["items"] == []
        assert len(client.get("/api/v1/comparisons", headers=ALICE).json()["items"]) == 1


def test_concepts_and_queries_only_see_own_policies(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path)) as client:
        alice_policy = _upload(client, ALICE)

        bob_occurrences = client.get("/api/v1/concepts/DO-015/occurrences", headers=BOB)
        assert bob_occurrences.status_code == 200
        assert bob_occurrences.json()["items"] == []
        bob_answer = client.post(
            "/api/v1/queries", headers=BOB, json={"question": "A Aurora cobre multas?"}
        ).json()
        assert bob_answer["matches"] == []

        alice_occurrences = client.get("/api/v1/concepts/DO-015/occurrences", headers=ALICE)
        assert {o["policy"]["id"] for o in alice_occurrences.json()["items"]} == {alice_policy}


def test_responses_expose_expires_at_but_never_the_owner(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path)) as client:
        policy_a, policy_b = _upload(client, ALICE), _upload(client, ALICE)
        comparison_id = _compare(client, ALICE, policy_a, policy_b)

        detail = client.get(f"/api/v1/policies/{policy_a}", headers=ALICE).json()
        summary = client.get("/api/v1/policies", headers=ALICE).json()["items"][0]
        comparison = client.get(f"/api/v1/comparisons/{comparison_id}", headers=ALICE).json()
        history = client.get("/api/v1/comparisons", headers=ALICE).json()["items"][0]

        for body in (detail, summary, comparison, history):
            assert "owner_id" not in body
            assert body["expires_at"].endswith("Z") or "+00:00" in body["expires_at"]
        expiries = [
            client.get(f"/api/v1/policies/{p}", headers=ALICE).json()["expires_at"]
            for p in (policy_a, policy_b)
        ]
        # The comparison expires with the earliest policy.
        assert comparison["expires_at"] == min(expiries)
        assert "alice" not in str(comparison)
