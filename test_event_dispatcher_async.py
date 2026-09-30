import asyncio

from event_dispatcher import EventDispatcher
from kernel_events import (
    EventStream,
    KernelEventType,
    create_event,
)


async def main():

    print("=" * 70)
    print("EVENT DISPATCHER ASYNC HANDLER TEST")
    print("=" * 70)

    event_stream = EventStream()
    dispatcher = EventDispatcher(event_stream)

    dispatcher.attach()

    received_events = []
    async_received_events = []
    failing_async_handler_called = False

    # --------------------------------------------------
    # SYNC HANDLER
    # --------------------------------------------------

    def sync_handler(event):

        received_events.append(
            event.event_type
        )

        print(
            f"[SYNC HANDLER] Received: "
            f"{event.event_type.value}"
        )

    # --------------------------------------------------
    # ASYNC HANDLER
    # --------------------------------------------------

    async def async_handler(event):

        await asyncio.sleep(0.05)

        async_received_events.append(
            event.event_type
        )

        print(
            f"[ASYNC HANDLER] Received: "
            f"{event.event_type.value}"
        )

    # --------------------------------------------------
    # FAILING ASYNC HANDLER
    # --------------------------------------------------

    async def failing_async_handler(event):

        nonlocal failing_async_handler_called

        failing_async_handler_called = True

        await asyncio.sleep(0.02)

        raise RuntimeError(
            "Intentional async handler failure."
        )

    # --------------------------------------------------
    # REGISTER HANDLERS
    # --------------------------------------------------

    dispatcher.subscribe(
        KernelEventType.TOOL_COMPLETED,
        sync_handler
    )

    dispatcher.subscribe(
        KernelEventType.TOOL_COMPLETED,
        async_handler
    )

    dispatcher.subscribe(
        KernelEventType.TOOL_COMPLETED,
        failing_async_handler
    )

    assert (
        dispatcher.handler_count(
            KernelEventType.TOOL_COMPLETED
        )
        == 3
    )

    # --------------------------------------------------
    # CREATE EVENT
    # --------------------------------------------------

    event = create_event(
        KernelEventType.TOOL_COMPLETED,
        task_id="async-test-task",
        tool_name="smart_home",
        data={
            "device": "bedroom_light",
            "state": "on"
        }
    )

    # --------------------------------------------------
    # EMIT EVENT
    # --------------------------------------------------

    event_stream.emit(event)

    # EventStream schedules async handlers.
    # Give them enough time to complete.
    await asyncio.sleep(0.2)

    # --------------------------------------------------
    # VERIFY SYNC HANDLER
    # --------------------------------------------------

    assert received_events == [
        KernelEventType.TOOL_COMPLETED
    ]

    # --------------------------------------------------
    # VERIFY ASYNC HANDLER
    # --------------------------------------------------

    assert async_received_events == [
        KernelEventType.TOOL_COMPLETED
    ]

    # --------------------------------------------------
    # VERIFY FAILING ASYNC HANDLER
    # --------------------------------------------------

    assert failing_async_handler_called is True

    # The failing async handler must not remove
    # or disable the other registered handlers.

    assert (
        dispatcher.handler_count(
            KernelEventType.TOOL_COMPLETED
        )
        == 3
    )

    # --------------------------------------------------
    # VERIFY DISPATCHER STILL WORKS
    # --------------------------------------------------

    received_events.clear()
    async_received_events.clear()
    failing_async_handler_called = False

    second_event = create_event(
        KernelEventType.TOOL_COMPLETED,
        task_id="async-test-task-2",
        tool_name="smart_home",
        data={
            "device": "living_room_light",
            "state": "on"
        }
    )

    event_stream.emit(second_event)

    await asyncio.sleep(0.2)

    assert received_events == [
        KernelEventType.TOOL_COMPLETED
    ]

    assert async_received_events == [
        KernelEventType.TOOL_COMPLETED
    ]

    assert failing_async_handler_called is True

    # --------------------------------------------------
    # DETACH
    # --------------------------------------------------

    dispatcher.detach()

    assert dispatcher._attached is False

    print()
    print("Sync handler received the event.")
    print("Async handler received the event.")
    print("Async handler failure was isolated.")
    print("Dispatcher remained functional.")
    print()
    print(
        "EVENT DISPATCHER ASYNC HANDLER "
        "TEST PASSED"
    )


if __name__ == "__main__":

    asyncio.run(main())