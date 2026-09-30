"""Deterministic identity for local development and tests (AUTH_BACKEND=fake).

A token `dev-<uid>` authenticates as `<uid>`. Settings refuse this adapter in production.
"""

import re

from app.domain.interfaces.ports import Identity
from app.shared.exceptions import AuthenticationError

FAKE_TOKEN = re.compile(r"dev-([A-Za-z0-9_-]{1,128})")


class FakeIdentityVerifier:
    def __init__(self) -> None:
        self.revoked: set[str] = set()

    async def verify(self, token: str, check_revoked: bool = False) -> Identity:
        match = FAKE_TOKEN.fullmatch(token)
        if match is None:
            raise AuthenticationError(
                "Não foi possível confirmar seu acesso. Recarregue a página.",
                code="AUTH_TOKEN_INVALID",
            )
        uid = match.group(1)
        if check_revoked and uid in self.revoked:
            raise AuthenticationError(
                "Seu acesso foi encerrado. Recarregue a página.", code="AUTH_TOKEN_REVOKED"
            )
        return Identity(uid=uid)


class FakeAccountRemover:
    def __init__(self) -> None:
        self.removed: list[str] = []

    async def remove(self, uid: str) -> None:
        self.removed.append(uid)
