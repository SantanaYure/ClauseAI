from app.domain.interfaces.events import Event
from app.infrastructure.events import InMemoryEventBus


async def test_publish_calls_subscriber_once() -> None:
    bus = InMemoryEventBus()
    received: list[str] = []

    async def handler(event: Event) -> None:
        received.append(event.event_id)

    event = Event.create("DocumentUploaded", "correlation-1", {"document_id": "doc-1"})
    bus.subscribe(event.event_type, handler)
    bus.subscribe(event.event_type, handler)

    await bus.publish(event)

    assert received == [event.event_id]


async def test_publish_attempts_all_subscribers_before_raising() -> None:
    bus = InMemoryEventBus()
    calls: list[str] = []

    async def failing_handler(event: Event) -> None:
        calls.append("failing")
        raise RuntimeError("handler failed")

    async def successful_handler(event: Event) -> None:
        calls.append("successful")

    event = Event.create("TestEvent", "correlation-1", {})
    bus.subscribe(event.event_type, failing_handler)
    bus.subscribe(event.event_type, successful_handler)

    try:
        await bus.publish(event)
    except RuntimeError as error:
        assert str(error) == "handler failed"
    else:
        raise AssertionError("Expected the handler error to be raised")

    assert calls == ["failing", "successful"]
