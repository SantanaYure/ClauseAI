"""Run an async action at startup and then at a fixed interval, until stopped."""

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from typing import Any

from app.shared.logging import error_fields, get_logger, log_context

logger = get_logger(__name__)


class PeriodicJob:
    """A failing run is logged and retried at the next interval; it never stops the loop."""

    def __init__(
        self, name: str, action: Callable[[], Awaitable[Any]], interval_seconds: float
    ) -> None:
        self._name = name
        self._action = action
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def run_once(self) -> None:
        try:
            await self._action()
        except Exception as exc:
            with log_context(job=self._name, **error_fields(exc)):
                logger.error("Periodic job failed")

    async def _loop(self) -> None:
        while True:
            await self.run_once()
            await asyncio.sleep(self._interval_seconds)
