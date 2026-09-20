"""Composition root for the ClauseAI API."""

from app.infrastructure.events import InMemoryEventBus
from app.presentation.api.app import create_app
from app.shared.config.settings import get_settings

settings = get_settings()
event_bus = InMemoryEventBus()
app = create_app(settings=settings, event_bus=event_bus)
