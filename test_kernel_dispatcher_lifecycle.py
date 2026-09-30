import asyncio

from kernel import Kernel
from kernel_events import KernelEventType


async def main():

    print("=" * 70)
    print("KERNEL → DISPATCHER LIFECYCLE EVENT TEST")
    print("=" * 70)

    kernel = Kernel()

    received_events = []

    # --------------------------------------------------
    # DISPATCHER HANDLER
    # --------------------------------------------------

    def handler(event):

        received_events.append(event.event_type)

        print(
            f"[DISPATCHER] "
            f"{event.event_type.value}"
        )

    # --------------------------------------------------
    # SUBSCRIBE TO FULL LIFECYCLE
    # --------------------------------------------------

    lifecycle_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TOOL_STARTED,
        KernelEventType.TOOL_COMPLETED,
        KernelEventType.CHECKPOINT_SAVED,
        KernelEventType.TASK_COMPLETED,
    ]

    for event_type in lifecycle_events:

        kernel.event_dispatcher.subscribe(
            event_type,
            handler
        )

    # --------------------------------------------------
    # START TASK
    # --------------------------------------------------

    task = kernel.start_task(
        "Search for a flight from Bengaluru to Delhi."
    )

    # --------------------------------------------------
    # EXECUTE TOOL
    # --------------------------------------------------

    result = await kernel.execute_tool(
        "flight_search",
        task.task_id,
        origin="Bengaluru",
        destination="Delhi",
    )

    assert result.success is True

    # --------------------------------------------------
    # SAVE CHECKPOINT
    # --------------------------------------------------

    kernel.save_checkpoint(
        "flight_search_completed",
        step_name="flight_search",
        result=result.data,
    )

    # --------------------------------------------------
    # COMPLETE TASK
    # --------------------------------------------------

    kernel.complete_current_task()

    # Give asynchronous dispatch operations time to finish.

    await asyncio.sleep(0.1)

    # --------------------------------------------------
    # EXPECTED EVENT ORDER
    # --------------------------------------------------

    expected_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TOOL_STARTED,
        KernelEventType.TOOL_COMPLETED,
        KernelEventType.CHECKPOINT_SAVED,
        KernelEventType.TASK_COMPLETED,
    ]

    assert received_events == expected_events, (
        f"\nExpected:\n{expected_events}"
        f"\nReceived:\n{received_events}"
    )

    # --------------------------------------------------
    # VERIFY EVENT STREAM
    # --------------------------------------------------

    stored_events = (
        kernel.event_stream.get_task_events(
            task.task_id
        )
    )

    stored_types = [
        event.event_type
        for event in stored_events
    ]

    assert stored_types == expected_events

    # --------------------------------------------------
    # VERIFY SAME TASK ID
    # --------------------------------------------------

    for event in stored_events:

        assert event.task_id == task.task_id

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    print()
    print(
        f"Dispatched lifecycle events: "
        f"{len(received_events)}"
    )

    print(
        f"Stored lifecycle events: "
        f"{len(stored_events)}"
    )

    print()
    print("TASK_STARTED       ✓")
    print("TOOL_STARTED       ✓")
    print("TOOL_COMPLETED     ✓")
    print("CHECKPOINT_SAVED   ✓")
    print("TASK_COMPLETED     ✓")

    print()
    print(
        "KERNEL → DISPATCHER LIFECYCLE "
        "EVENT TEST PASSED"
    )


if __name__ == "__main__":
    asyncio.run(main())