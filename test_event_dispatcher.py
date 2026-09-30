import asyncio

from event_dispatcher import EventDispatcher
from kernel_events import (
    EventStream,
    KernelEventType,
    create_event,
)


async def main():

    print("=" * 70)
    print("EVENT DISPATCHER REGRESSION TEST")
    print("=" * 70)

    stream = EventStream()
    dispatcher = EventDispatcher(stream)

    sync_received = []
    async_received = []
    failing_called = False

    # --------------------------------------------------
    # HANDLERS
    # --------------------------------------------------

    def sync_handler(event):

        sync_received.append(event.event_type)

        print(
            f"[SYNC] {event.event_type.value}"
        )

    async def async_handler(event):

        await asyncio.sleep(0.02)

        async_received.append(event.event_type)

        print(
            f"[ASYNC] {event.event_type.value}"
        )

    async def failing_handler(event):

        nonlocal failing_called

        failing_called = True

        await asyncio.sleep(0.01)

        raise RuntimeError(
            "Intentional regression-test failure."
        )

    # --------------------------------------------------
    # ATTACH
    # --------------------------------------------------

    dispatcher.attach()
    dispatcher.attach()

    assert dispatcher._attached is True
    assert stream.subscriber_count() == 1

    # --------------------------------------------------
    # REGISTER
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
        failing_handler
    )

    assert (
        dispatcher.handler_count(
            KernelEventType.TOOL_COMPLETED
        )
        == 3
    )

    # --------------------------------------------------
    # FIRST EVENT
    # --------------------------------------------------

    event = create_event(
        KernelEventType.TOOL_COMPLETED,
        task_id="regression-task-1",
        tool_name="smart_home",
        data={
            "device": "bedroom_light",
            "state": "on",
        },
    )

    stream.emit(event)

    await asyncio.sleep(0.1)

    assert sync_received == [
        KernelEventType.TOOL_COMPLETED
    ]

    assert async_received == [
        KernelEventType.TOOL_COMPLETED
    ]

    assert failing_called is True

    # --------------------------------------------------
    # FAILURE MUST NOT REMOVE HANDLERS
    # --------------------------------------------------

    assert (
        dispatcher.handler_count(
            KernelEventType.TOOL_COMPLETED
        )
        == 3
    )

    # --------------------------------------------------
    # UNSUBSCRIBE FAILING HANDLER
    # --------------------------------------------------

    dispatcher.unsubscribe(
        KernelEventType.TOOL_COMPLETED,
        failing_handler
    )

    assert (
        dispatcher.handler_count(
            KernelEventType.TOOL_COMPLETED
        )
        == 2
    )

    # --------------------------------------------------
    # SECOND EVENT
    # --------------------------------------------------

    sync_received.clear()
    async_received.clear()
    failing_called = False

    second_event = create_event(
        KernelEventType.TOOL_COMPLETED,
        task_id="regression-task-2",
        tool_name="smart_home",
        data={
            "device": "living_room_light",
            "state": "off",
        },
    )

    stream.emit(second_event)

    await asyncio.sleep(0.1)

    assert sync_received == [
        KernelEventType.TOOL_COMPLETED
    ]

    assert async_received == [
        KernelEventType.TOOL_COMPLETED
    ]

    assert failing_called is False

    # --------------------------------------------------
    # DETACH
    # --------------------------------------------------

    dispatcher.detach()

    assert dispatcher._attached is False
    assert stream.subscriber_count() == 0

    # --------------------------------------------------
    # EVENT AFTER DETACH
    # --------------------------------------------------

    sync_received.clear()
    async_received.clear()

    stream.emit(
        create_event(
            KernelEventType.TOOL_COMPLETED,
            task_id="regression-task-3",
            tool_name="smart_home",
        )
    )

    await asyncio.sleep(0.05)

    assert sync_received == []
    assert async_received == []

    # --------------------------------------------------
    # FINAL CHECKS
    # --------------------------------------------------

    assert (
        dispatcher.handler_count(
            KernelEventType.TOOL_COMPLETED
        )
        == 2
    )

    print()
    print("Attach/detach: PASSED")
    print("Sync handlers: PASSED")
    print("Async handlers: PASSED")
    print("Failure isolation: PASSED")
    print("Unsubscribe: PASSED")
    print("Duplicate attach protection: PASSED")
    print("Post-detach isolation: PASSED")
    print()
    print(
        "EVENT DISPATCHER REGRESSION TEST PASSED"
    )


if __name__ == "__main__":
    asyncio.run(main())