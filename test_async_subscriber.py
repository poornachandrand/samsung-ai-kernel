import asyncio

from kernel import Kernel
from kernel_events import KernelEventType
from tools import SmartHomeTool


# ==========================================================
# TEST: ASYNC EVENT SUBSCRIBER
# ==========================================================

async def test_async_subscriber():

    print()
    print("=" * 70)
    print(
        "             ASYNC SUBSCRIBER TEST"
    )
    print("=" * 70)

    # ------------------------------------------------------
    # CREATE KERNEL
    # ------------------------------------------------------

    kernel = Kernel()

    received_events = []

    # ------------------------------------------------------
    # ASYNC SUBSCRIBER
    # ------------------------------------------------------

    async def async_listener(event):

        # Simulate asynchronous work.
        await asyncio.sleep(0.01)

        received_events.append(
            event
        )

        print(
            f"[ASYNC LISTENER] "
            f"{event.event_type.value}"
        )

    # ------------------------------------------------------
    # SUBSCRIBE
    # ------------------------------------------------------

    kernel.event_stream.subscribe(
        async_listener
    )

    assert (
        kernel.event_stream.subscriber_count()
        == 1
    )

    # ------------------------------------------------------
    # REGISTER TOOL
    # ------------------------------------------------------

    kernel.register_tool(
        SmartHomeTool()
    )

    # ------------------------------------------------------
    # START TASK
    # ------------------------------------------------------

    task = kernel.start_task(
        "Turn on bedroom light."
    )

    # ------------------------------------------------------
    # EXECUTE TOOL
    # ------------------------------------------------------

    result = await kernel.execute_tool(
        "smart_home",
        task.task_id,
        action="turn_on",
        device="bedroom_light"
    )

    assert result.success is True

    # ------------------------------------------------------
    # COMPLETE TASK
    # ------------------------------------------------------

    kernel.complete_current_task()

    # ------------------------------------------------------
    # GIVE ASYNC SUBSCRIBERS TIME TO FINISH
    # ------------------------------------------------------

    await asyncio.sleep(
        0.1
    )

    # ------------------------------------------------------
    # VERIFY EVENTS
    # ------------------------------------------------------

    event_types = [
        event.event_type
        for event in received_events
    ]

    print()
    print(
        "Events received by async subscriber:"
    )

    for event_type in event_types:

        print(
            f"- {event_type.value}"
        )

    expected_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TOOL_STARTED,
        KernelEventType.TOOL_COMPLETED,
        KernelEventType.TASK_COMPLETED,
    ]

    assert (
        event_types
        == expected_events
    )

    # ------------------------------------------------------
    # VERIFY EVENT STORAGE
    # ------------------------------------------------------

    stored_events = (
        kernel.event_stream.get_task_events(
            task.task_id
        )
    )

    assert len(
        stored_events
    ) == 4

    # ------------------------------------------------------
    # UNSUBSCRIBE
    # ------------------------------------------------------

    kernel.event_stream.unsubscribe(
        async_listener
    )

    assert (
        kernel.event_stream.subscriber_count()
        == 0
    )

    # ------------------------------------------------------
    # OUTPUT
    # ------------------------------------------------------

    print()
    print(
        "Async events received:",
        len(received_events)
    )

    print(
        "Stored events:",
        len(stored_events)
    )

    print(
        "Subscribers remaining:",
        kernel.event_stream.subscriber_count()
    )

    print()
    print(
        "ASYNC SUBSCRIBER TEST PASSED"
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    asyncio.run(
        test_async_subscriber()
    )