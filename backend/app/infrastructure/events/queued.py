"""Queued EventBus: publishing returns immediately and a worker task consumes
events in the background (ADR-012, ADR-014, SPEC-014)."""

import asyncio
import contextlib

from app.domain.interfaces.events import Event, EventBus, EventHandler
from app.infrastructure.events.in_memory import InMemoryEventBus
from app.shared.logging import error_fields, get_logger, log_context

logger = get_logger(__name__)


class QueuedEventBus(EventBus):
    """Wraps InMemoryEventBus with an asyncio.Queue and N worker tasks.

    Not durable: events queued when the process stops are lost. The state is
    persisted before publishing, so the job can be retried from the API.
    """

    def __init__(self, workers: int = 2) -> None:
        self._inner = InMemoryEventBus()
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._workers = workers
        self._tasks: list[asyncio.Task[None]] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._inner.subscribe(event_type, handler)

    async def publish(self, event: Event) -> None:
        await self._queue.put(event)

    async def start(self) -> None:
        if not self._tasks:
            self._tasks = [asyncio.create_task(self._work()) for _ in range(self._workers)]

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks = []

    async def drain(self) -> None:
        """Wait until every queued event was handled (used by tests)."""

        await self._queue.join()

    async def _work(self) -> None:
        while True:
            event = await self._queue.get()
            try:
                await self._inner.publish(event)
            except Exception as exc:  # handlers record their own failures
                with log_context(**error_fields(exc)):
                    logger.error("Event processing failed")
            finally:
                self._queue.task_done()
