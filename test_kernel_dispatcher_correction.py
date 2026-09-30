import asyncio

from kernel import Kernel
from kernel_events import KernelEventType


async def main():

    print("=" * 70)
    print("KERNEL → DISPATCHER CORRECTION EVENT TEST")
    print("=" * 70)

    kernel = Kernel()

    received_events = []

    # --------------------------------------------------
    # DISPATCHER HANDLER
    # --------------------------------------------------

    def handler(event):

        received_events.append(
            (
                event.event_type,
                event.task_id
            )
        )

        print(
            f"[DISPATCHER] "
            f"{event.event_type.value}"
        )

    # --------------------------------------------------
    # SUBSCRIBE
    # --------------------------------------------------

    lifecycle_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_CANCELLED,
        KernelEventType.TASK_COMPLETED,
    ]

    for event_type in lifecycle_events:

        kernel.event_dispatcher.subscribe(
            event_type,
            handler
        )

    # --------------------------------------------------
    # START ORIGINAL TASK
    # --------------------------------------------------

    original_task = kernel.start_task(
        "Find flights from Bengaluru to Delhi."
    )

    original_task_id = original_task.task_id

    # --------------------------------------------------
    # APPLY USER CORRECTION
    #
    # The current Kernel implementation:
    #
    # 1. Cancels the original task.
    # 2. Creates a new corrected task.
    #
    # handle_user_correction() does not need to
    # return True.
    # --------------------------------------------------

    corrected_task = kernel.handle_user_correction(
        "Actually, find flights from Bengaluru to Mumbai."
    )

    # --------------------------------------------------
    # VERIFY NEW TASK
    # --------------------------------------------------

    assert corrected_task is not None

    corrected_task_id = corrected_task.task_id

    assert corrected_task_id != original_task_id

    # --------------------------------------------------
    # COMPLETE CORRECTED TASK
    # --------------------------------------------------

    kernel.complete_current_task()

    await asyncio.sleep(0.1)

    # --------------------------------------------------
    # EXPECTED EVENT ORDER
    # --------------------------------------------------

    expected_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_CANCELLED,
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_COMPLETED,
    ]

    received_types = [
        event_type
        for event_type, task_id in received_events
    ]

    assert received_types == expected_events, (
        f"\nExpected:\n{expected_events}"
        f"\nReceived:\n{received_types}"
    )

    # --------------------------------------------------
    # VERIFY ORIGINAL TASK EVENTS
    # --------------------------------------------------

    original_events = (
        kernel.event_stream.get_task_events(
            original_task_id
        )
    )

    original_types = [
        event.event_type
        for event in original_events
    ]

    assert original_types == [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_CANCELLED,
    ]

    # --------------------------------------------------
    # VERIFY CORRECTED TASK EVENTS
    # --------------------------------------------------

    corrected_events = (
        kernel.event_stream.get_task_events(
            corrected_task_id
        )
    )

    corrected_types = [
        event.event_type
        for event in corrected_events
    ]

    assert corrected_types == [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_COMPLETED,
    ]

    # --------------------------------------------------
    # VERIFY TASK ISOLATION
    # --------------------------------------------------

    for event in original_events:

        assert event.task_id == original_task_id

    for event in corrected_events:

        assert event.task_id == corrected_task_id

    # --------------------------------------------------
    # VERIFY CORRECTED GOAL
    # --------------------------------------------------

    assert (
        corrected_task.goal
        == "Actually, find flights from Bengaluru to Mumbai."
    )

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    print()
    print(
        f"Original task:  {original_task_id}"
    )

    print(
        f"Corrected task: {corrected_task_id}"
    )

    print()
    print("Original TASK_STARTED       ✓")
    print("Original TASK_CANCELLED     ✓")
    print("Corrected TASK_STARTED      ✓")
    print("Corrected TASK_COMPLETED    ✓")
    print("Task isolation              ✓")
    print("Corrected goal              ✓")

    print()
    print(
        "KERNEL → DISPATCHER CORRECTION "
        "EVENT TEST PASSED"
    )


if __name__ == "__main__":
    asyncio.run(main())