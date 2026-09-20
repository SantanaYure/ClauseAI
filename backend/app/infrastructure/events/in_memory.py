"""In-process EventBus for the MVP foundation."""

import asyncio
from collections import defaultdict

from app.domain.interfaces.events import Event, EventBus, EventHandler
from app.shared.logging import get_logger, log_context


class InMemoryEventBus(EventBus):
    """Async event bus with process-local subscriptions.

    It intentionally provides no durability or delivery guarantees beyond the
    current process. Handlers are still registered through the domain port so
    a durable implementation can replace this class later.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._logger = get_logger(__name__)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler once for an event type."""

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        """Run all handlers for an event and surface the first failure.

        Every subscribed handler is attempted so one failure does not silently
        skip the remaining consumers. The first error is re-raised after all
        handlers finish, allowing the caller to record a failed dispatch.
        """

        handlers = tuple(self._handlers.get(event.event_type, ()))
        if not handlers:
            return

        failures: list[BaseException] = []
        with log_context(event_id=event.event_id, correlation_id=event.correlation_id):
            results = await asyncio.gather(
                *(handler(event) for handler in handlers),
                return_exceptions=True,
            )
        for result in results:
            if isinstance(result, BaseException):
                failures.append(result)
                self._logger.exception(
                    "Event handler failed",
                    exc_info=(type(result), result, result.__traceback__),
                )
        if failures:
            raise failures[0]
