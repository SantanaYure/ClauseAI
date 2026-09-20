"""Event infrastructure public API."""

from app.infrastructure.events.in_memory import InMemoryEventBus

__all__ = ["InMemoryEventBus"]
