import asyncio

from kernel import Kernel
from kernel_events import KernelEventType
from tools import SmartHomeTool


# ==========================================================
# TEST: KERNEL → EVENT SUBSCRIBER
# ==========================================================

async def test_kernel_event_subscriber():

    print()
    print("=" * 70)
    print(
        "      KERNEL → EVENT SUBSCRIBER TEST"
    )
    print("=" * 70)

    # ------------------------------------------------------
    # CREATE KERNEL
    # ------------------------------------------------------

    kernel = Kernel()

    received_events = []

    # ------------------------------------------------------
    # CREATE SUBSCRIBER
    # ------------------------------------------------------

    def event_listener(event):

        received_events.append(event)

        print(
            f"[LISTENER] "
            f"{event.event_type.value}"
        )

    # ------------------------------------------------------
    # SUBSCRIBE
    # ------------------------------------------------------

    kernel.event_stream.subscribe(
        event_listener
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
    # VERIFY TASK STARTED
    # ------------------------------------------------------

    assert len(
        received_events
    ) >= 1

    assert (
        received_events[0].event_type
        == KernelEventType.TASK_STARTED
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
    # VERIFY EVENT SEQUENCE
    # ------------------------------------------------------

    event_types = [
        event.event_type
        for event in received_events
    ]

    print()
    print(
        "Events received by subscriber:"
    )

    for event_type in event_types:

        print(
            f"- {event_type.value}"
        )

    # ------------------------------------------------------
    # VERIFY REQUIRED EVENTS
    # ------------------------------------------------------

    assert (
        KernelEventType.TASK_STARTED
        in event_types
    )

    assert (
        KernelEventType.TOOL_STARTED
        in event_types
    )

    assert (
        KernelEventType.TOOL_COMPLETED
        in event_types
    )

    assert (
        KernelEventType.TASK_COMPLETED
        in event_types
    )

    # ------------------------------------------------------
    # VERIFY EVENT ORDER
    # ------------------------------------------------------

    task_started_index = (
        event_types.index(
            KernelEventType.TASK_STARTED
        )
    )

    tool_started_index = (
        event_types.index(
            KernelEventType.TOOL_STARTED
        )
    )

    tool_completed_index = (
        event_types.index(
            KernelEventType.TOOL_COMPLETED
        )
    )

    task_completed_index = (
        event_types.index(
            KernelEventType.TASK_COMPLETED
        )
    )

    assert (
        task_started_index
        < tool_started_index
        < tool_completed_index
        < task_completed_index
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
    ) == len(
        received_events
    )

    # ------------------------------------------------------
    # UNSUBSCRIBE
    # ------------------------------------------------------

    kernel.event_stream.unsubscribe(
        event_listener
    )

    assert (
        kernel.event_stream.subscriber_count()
        == 0
    )

    # ------------------------------------------------------
    # FINAL OUTPUT
    # ------------------------------------------------------

    print()
    print(
        "Total events received:",
        len(received_events)
    )

    print(
        "Total events stored:",
        len(stored_events)
    )

    print(
        "Subscribers after unsubscribe:",
        kernel.event_stream.subscriber_count()
    )

    print()
    print(
        "KERNEL → EVENT SUBSCRIBER TEST PASSED"
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    asyncio.run(
        test_kernel_event_subscriber()
    )