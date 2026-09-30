"""Rate limiting adapters."""

from app.infrastructure.quotas.sliding_window import SlidingWindowRateLimiter

__all__ = ["SlidingWindowRateLimiter"]
