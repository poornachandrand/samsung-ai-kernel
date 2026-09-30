import asyncio

from kernel import Kernel
from kernel_events import KernelEventType


async def main():

    print("=" * 70)
    print("KERNEL → DISPATCHER CANCELLATION EVENT TEST")
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
    # SUBSCRIBE
    # --------------------------------------------------

    kernel.event_dispatcher.subscribe(
        KernelEventType.TASK_STARTED,
        handler
    )

    kernel.event_dispatcher.subscribe(
        KernelEventType.TASK_CANCELLED,
        handler
    )

    # --------------------------------------------------
    # START TASK
    # --------------------------------------------------

    task = kernel.start_task(
        "Search for flights from Bengaluru to Delhi."
    )

    # --------------------------------------------------
    # CANCEL CURRENT TASK
    # --------------------------------------------------

    kernel.cancel_current_task()

    await asyncio.sleep(0.1)

    # --------------------------------------------------
    # EXPECTED EVENTS
    # --------------------------------------------------

    expected_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_CANCELLED,
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
    # VERIFY TASK ID
    # --------------------------------------------------

    for event in stored_events:

        assert event.task_id == task.task_id

    # --------------------------------------------------
    # VERIFY CANCELLATION EVENT
    # --------------------------------------------------

    cancelled_event = next(
        event
        for event in stored_events
        if event.event_type
        == KernelEventType.TASK_CANCELLED
    )

    assert cancelled_event.task_id == task.task_id

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    print()
    print(
        f"Dispatched events: "
        f"{len(received_events)}"
    )

    print(
        f"Stored events: "
        f"{len(stored_events)}"
    )

    print()
    print("TASK_STARTED        ✓")
    print("TASK_CANCELLED      ✓")
    print("Task ID consistency ✓")

    print()
    print(
        "KERNEL → DISPATCHER CANCELLATION "
        "EVENT TEST PASSED"
    )


if __name__ == "__main__":
    asyncio.run(main())