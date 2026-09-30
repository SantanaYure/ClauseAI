"""Sliding-window rate limiter kept in process memory.

Valid for the single-instance deployment (render.yaml runs one process); a restart
clears the windows. A shared store would be needed to scale horizontally.
"""

import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import timedelta


class SlidingWindowRateLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window: timedelta) -> bool:
        now = self._clock()
        hits = self._hits[key]
        while hits and now - hits[0] >= window.total_seconds():
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True
