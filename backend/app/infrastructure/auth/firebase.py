"""Firebase Auth adapters (anonymous accounts created by the browser).

Firebase error details never reach the client or the logs: each failure is mapped
to a stable public code.
"""

import asyncio
from typing import Any

from app.domain.interfaces.ports import Identity
from app.shared.exceptions import AuthenticationError, InfrastructureError

_EXPIRED = ("Seu acesso expirou. Recarregue a página.", "AUTH_TOKEN_EXPIRED")
_INVALID = ("Não foi possível confirmar seu acesso. Recarregue a página.", "AUTH_TOKEN_INVALID")
_REVOKED = ("Seu acesso foi encerrado. Recarregue a página.", "AUTH_TOKEN_REVOKED")


def _auth_error(message_and_code: tuple[str, str]) -> AuthenticationError:
    message, code = message_and_code
    return AuthenticationError(message, code=code)


def _unavailable() -> InfrastructureError:
    return InfrastructureError(
        "Não foi possível confirmar seu acesso agora. Tente novamente em instantes.",
        code="AUTH_UNAVAILABLE",
        details={"retryable": True},
    )


class FirebaseIdentityVerifier:
    def __init__(self, firebase_app: Any, clock_skew_seconds: int = 10) -> None:
        self._app = firebase_app
        self._clock_skew_seconds = clock_skew_seconds

    async def verify(self, token: str, check_revoked: bool = False) -> Identity:
        claims = await self._verify(token, check_revoked=False)
        identity = Identity(uid=str(claims["uid"]))
        if check_revoked:
            await self._ensure_not_revoked(token)
        return identity

    async def _ensure_not_revoked(self, token: str) -> None:
        try:
            await self._verify(token, check_revoked=True)
        except _UserNotFound:
            # The account was already removed (e.g. a repeated "delete my data"): the
            # token is still genuine for this uid, so the caller may finish the cleanup.
            return

    async def _verify(self, token: str, check_revoked: bool) -> dict[str, Any]:
        from firebase_admin import auth, exceptions

        try:
            claims: dict[str, Any] = await asyncio.to_thread(
                auth.verify_id_token,
                token,
                app=self._app,
                check_revoked=check_revoked,
                clock_skew_seconds=self._clock_skew_seconds,
            )
        except auth.ExpiredIdTokenError:
            raise _auth_error(_EXPIRED) from None
        except (auth.RevokedIdTokenError, auth.UserDisabledError):
            raise _auth_error(_REVOKED) from None
        except auth.UserNotFoundError:
            raise _UserNotFound from None
        except (auth.InvalidIdTokenError, ValueError):
            raise _auth_error(_INVALID) from None
        except (auth.CertificateFetchError, exceptions.FirebaseError):
            raise _unavailable() from None
        return claims


class _UserNotFound(Exception):
    """The token is valid but its anonymous account no longer exists."""


class FirebaseAccountRemover:
    def __init__(self, firebase_app: Any) -> None:
        self._app = firebase_app

    async def remove(self, uid: str) -> None:
        from firebase_admin import auth

        try:
            await asyncio.to_thread(auth.delete_user, uid, app=self._app)
        except auth.UserNotFoundError:
            return
        except Exception:
            raise _unavailable() from None
