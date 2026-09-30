"""Firebase Auth errors map to stable public codes, without Firebase details."""

from typing import Any

import pytest
from app.infrastructure.auth import FirebaseAccountRemover, FirebaseIdentityVerifier
from app.shared.exceptions import ApplicationError
from firebase_admin import auth

SECRET_DETAIL = "detalhe interno do firebase"


def _patch_verify(monkeypatch: pytest.MonkeyPatch, effect: Any) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def verify_id_token(token: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        result = effect(kwargs) if callable(effect) else effect
        if isinstance(result, BaseException):
            raise result
        return result  # type: ignore[no-any-return]

    monkeypatch.setattr(auth, "verify_id_token", verify_id_token)
    return calls


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (auth.ExpiredIdTokenError(SECRET_DETAIL, cause=None), 401, "AUTH_TOKEN_EXPIRED"),
        (auth.InvalidIdTokenError(SECRET_DETAIL), 401, "AUTH_TOKEN_INVALID"),
        (ValueError(SECRET_DETAIL), 401, "AUTH_TOKEN_INVALID"),
        (auth.RevokedIdTokenError(SECRET_DETAIL), 401, "AUTH_TOKEN_REVOKED"),
        (auth.UserDisabledError(SECRET_DETAIL), 401, "AUTH_TOKEN_REVOKED"),
        (auth.CertificateFetchError(SECRET_DETAIL, cause=None), 503, "AUTH_UNAVAILABLE"),
    ],
)
async def test_errors_are_classified_and_sanitized(
    monkeypatch: pytest.MonkeyPatch, error: Exception, status: int, code: str
) -> None:
    _patch_verify(monkeypatch, error)

    with pytest.raises(ApplicationError) as raised:
        await FirebaseIdentityVerifier(firebase_app=object()).verify("token")

    assert (raised.value.status_code, raised.value.code) == (status, code)
    assert SECRET_DETAIL not in raised.value.message
    assert raised.value.__cause__ is None


async def test_valid_token_returns_the_uid_with_clock_skew(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_verify(monkeypatch, {"uid": "anon-123"})

    identity = await FirebaseIdentityVerifier(object(), clock_skew_seconds=10).verify("token")

    assert identity.uid == "anon-123"
    assert calls == [{"app": calls[0]["app"], "check_revoked": False, "clock_skew_seconds": 10}]


async def test_revocation_check_rejects_revoked_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    def effect(kwargs: dict[str, Any]) -> Any:
        return auth.RevokedIdTokenError("x") if kwargs["check_revoked"] else {"uid": "u1"}

    _patch_verify(monkeypatch, effect)

    with pytest.raises(ApplicationError) as raised:
        await FirebaseIdentityVerifier(object()).verify("token", check_revoked=True)
    assert raised.value.code == "AUTH_TOKEN_REVOKED"


async def test_revocation_check_tolerates_an_already_removed_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def effect(kwargs: dict[str, Any]) -> Any:
        return auth.UserNotFoundError("x") if kwargs["check_revoked"] else {"uid": "u1"}

    _patch_verify(monkeypatch, effect)

    identity = await FirebaseIdentityVerifier(object()).verify("token", check_revoked=True)
    assert identity.uid == "u1"


async def test_account_removal_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    removed: list[str] = []

    def delete_user(uid: str, app: Any = None) -> None:
        if uid in removed:
            raise auth.UserNotFoundError("x")
        removed.append(uid)

    monkeypatch.setattr(auth, "delete_user", delete_user)
    remover = FirebaseAccountRemover(object())

    await remover.remove("u1")
    await remover.remove("u1")

    assert removed == ["u1"]
