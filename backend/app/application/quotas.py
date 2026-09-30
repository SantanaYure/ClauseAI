"""Per-owner usage quotas (abuse protection for the anonymous, free service)."""

from dataclasses import dataclass
from datetime import timedelta

from app.application.errors import quota_exceeded
from app.domain.interfaces.ports import RateLimiter

HOUR = timedelta(hours=1)


@dataclass(frozen=True, slots=True)
class QuotaLimits:
    max_active_policies: int
    uploads_per_hour: int
    comparisons_per_hour: int


class QuotaGuard:
    def __init__(self, limiter: RateLimiter, limits: QuotaLimits) -> None:
        self._limiter = limiter
        self._limits = limits

    @property
    def max_active_policies(self) -> int:
        return self._limits.max_active_policies

    def ensure_room_for_policy(self, active_policies: int) -> None:
        limit = self._limits.max_active_policies
        if active_policies >= limit:
            raise quota_exceeded(
                "active_policies",
                f"Você já tem {limit} apólices guardadas neste navegador, o máximo permitido. "
                "Exclua alguma para enviar outra.",
            )

    def consume_upload(self, owner_id: str) -> None:
        limit = self._limits.uploads_per_hour
        if not self._limiter.allow(f"upload:{owner_id}", limit, HOUR):
            raise quota_exceeded(
                "uploads_per_hour",
                f"Você atingiu o limite de {limit} envios por hora. Tente novamente mais tarde.",
            )

    def consume_comparison(self, owner_id: str) -> None:
        limit = self._limits.comparisons_per_hour
        if not self._limiter.allow(f"comparison:{owner_id}", limit, HOUR):
            raise quota_exceeded(
                "comparisons_per_hour",
                f"Você atingiu o limite de {limit} comparações por hora. "
                "Tente novamente mais tarde.",
            )
