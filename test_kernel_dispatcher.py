import asyncio

from kernel import Kernel
from kernel_events import KernelEventType


async def main():

    print("=" * 70)
    print("KERNEL → EVENT DISPATCHER INTEGRATION TEST")
    print("=" * 70)

    kernel = Kernel()

    received_events = []

    # --------------------------------------------------
    # DISPATCHER HANDLER
    # --------------------------------------------------

    def event_handler(event):

        received_events.append(
            event.event_type
        )

        print(
            f"[DISPATCHER RECEIVED] "
            f"{event.event_type.value}"
        )

    # --------------------------------------------------
    # REGISTER HANDLER
    # --------------------------------------------------

    kernel.event_dispatcher.subscribe(
        KernelEventType.TASK_STARTED,
        event_handler
    )

    kernel.event_dispatcher.subscribe(
        KernelEventType.TOOL_STARTED,
        event_handler
    )

    kernel.event_dispatcher.subscribe(
        KernelEventType.TOOL_COMPLETED,
        event_handler
    )

    kernel.event_dispatcher.subscribe(
        KernelEventType.TASK_COMPLETED,
        event_handler
    )

    # --------------------------------------------------
    # RUN REAL KERNEL WORKFLOW
    # --------------------------------------------------

    task = kernel.start_task(
        "Turn on the bedroom light."
    )

    result = await kernel.execute_tool(
        "smart_home",
        task.task_id,
        action="turn_on",
        device="bedroom_light"
    )

    assert result.success is True

    kernel.complete_current_task()

    # Give async dispatcher handlers time if needed.
    await asyncio.sleep(0.1)

    # --------------------------------------------------
    # VERIFY EVENTS
    # --------------------------------------------------

    expected_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TOOL_STARTED,
        KernelEventType.TOOL_COMPLETED,
        KernelEventType.TASK_COMPLETED,
    ]

    assert received_events == expected_events, (
        f"Unexpected dispatcher events: "
        f"{received_events}"
    )

    # --------------------------------------------------
    # VERIFY EVENT STREAM
    # --------------------------------------------------

    stored_events = (
        kernel.event_stream.get_task_events(
            task.task_id
        )
    )

    assert len(stored_events) == 4

    stored_types = [
        event.event_type
        for event in stored_events
    ]

    assert stored_types == expected_events

    # --------------------------------------------------
    # VERIFY DISPATCHER
    # --------------------------------------------------

    assert (
        kernel.event_dispatcher.handler_count()
        == 4
    )

    print()
    print(
        f"Dispatcher received: "
        f"{len(received_events)} events"
    )

    print(
        f"EventStream stored: "
        f"{len(stored_events)} events"
    )

    print(
        f"Registered handlers: "
        f"{kernel.event_dispatcher.handler_count()}"
    )

    print()
    print(
        "KERNEL → EVENT DISPATCHER "
        "INTEGRATION TEST PASSED"
    )


if __name__ == "__main__":

    asyncio.run(main())