"""Framework-independent event contracts."""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Event:
    """Versioned event envelope shared by future application workflows."""

    event_id: str
    event_type: str
    occurred_at: datetime
    correlation_id: str
    payload: Mapping[str, Any]
    version: int = 1

    @classmethod
    def create(
        cls,
        event_type: str,
        correlation_id: str,
        payload: Mapping[str, Any],
        *,
        version: int = 1,
    ) -> "Event":
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            occurred_at=datetime.now(UTC),
            correlation_id=correlation_id,
            payload=payload,
            version=version,
        )


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus(Protocol):
    """Small port for publishing and subscribing to internal events."""

    async def publish(self, event: Event) -> None:
        """Publish an event to handlers subscribed to its type."""

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to one event type."""
