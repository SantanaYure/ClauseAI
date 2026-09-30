"""Per-owner quotas answer 429 QUOTA_EXCEEDED with a Portuguese message."""

from datetime import timedelta
from pathlib import Path

from app.application.quotas import QuotaLimits
from app.infrastructure.quotas import SlidingWindowRateLimiter
from fastapi.testclient import TestClient

from tests.fakes import PDF_BYTES, auth_headers, build_test_app
from tests.integration.test_owner_isolation import ALICE, BOB, _upload


def _post_policy(client: TestClient, headers: dict[str, str]) -> object:
    return client.post(
        "/api/v1/policies",
        headers=headers,
        data={"document_types": ["POLICY"]},
        files=[("files", ("a.pdf", PDF_BYTES, "application/pdf"))],
    )


def _limits(**overrides: int) -> QuotaLimits:
    values = {"max_active_policies": 50, "uploads_per_hour": 50, "comparisons_per_hour": 50}
    return QuotaLimits(**{**values, **overrides})


def _assert_quota(response: object, quota: str) -> None:
    assert response.status_code == 429  # type: ignore[attr-defined]
    error = response.json()["error"]  # type: ignore[attr-defined]
    assert error["code"] == "QUOTA_EXCEEDED"
    assert error["details"] == {"quota": quota}
    assert "limite" in error["message"] or "máximo" in error["message"]


def test_upload_rate_is_limited_per_owner(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path, quota_limits=_limits(uploads_per_hour=2))) as client:
        assert _post_policy(client, ALICE).status_code == 202  # type: ignore[attr-defined]
        assert _post_policy(client, ALICE).status_code == 202  # type: ignore[attr-defined]
        _assert_quota(_post_policy(client, ALICE), "uploads_per_hour")
        assert _post_policy(client, BOB).status_code == 202  # type: ignore[attr-defined]


def test_rejected_files_do_not_consume_the_upload_quota(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path, quota_limits=_limits(uploads_per_hour=1))) as client:
        bad = client.post(
            "/api/v1/policies",
            headers=ALICE,
            data={"document_types": ["POLICY"]},
            files=[("files", ("a.txt", b"texto", "text/plain"))],
        )
        assert bad.status_code == 415
        assert _post_policy(client, ALICE).status_code == 202  # type: ignore[attr-defined]


def test_active_policies_are_capped(tmp_path: Path) -> None:
    with TestClient(
        build_test_app(tmp_path, quota_limits=_limits(max_active_policies=1))
    ) as client:
        policy_id = _upload(client, ALICE)
        _assert_quota(_post_policy(client, ALICE), "active_policies")

        assert client.delete(f"/api/v1/policies/{policy_id}", headers=ALICE).status_code == 204
        assert _post_policy(client, ALICE).status_code == 202  # type: ignore[attr-defined]


def test_comparison_rate_is_limited(tmp_path: Path) -> None:
    app = build_test_app(tmp_path, quota_limits=_limits(comparisons_per_hour=1))
    with TestClient(app) as client:
        first, second = _upload(client, ALICE), _upload(client, ALICE)
        body = {"policy_a_id": first, "policy_b_id": second}
        assert client.post("/api/v1/comparisons", headers=ALICE, json=body).status_code == 202
        _assert_quota(
            client.post("/api/v1/comparisons", headers=ALICE, json=body), "comparisons_per_hour"
        )
        # A comparison with someone else's policy is still a 404, not a quota answer.
        other = client.post("/api/v1/comparisons", headers=auth_headers("carol"), json=body)
        assert other.status_code == 404


def test_sliding_window_frees_slots_after_the_window() -> None:
    now = [0.0]
    limiter = SlidingWindowRateLimiter(clock=lambda: now[0])
    hour = timedelta(hours=1)

    assert limiter.allow("k", 2, hour)
    assert limiter.allow("k", 2, hour)
    assert not limiter.allow("k", 2, hour)
    assert limiter.allow("other", 2, hour)

    now[0] = 3600.0
    assert limiter.allow("k", 2, hour)
