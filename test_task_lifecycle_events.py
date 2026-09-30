import asyncio

from kernel import Kernel, TaskStatus
from kernel_events import KernelEventType


async def main():

    print("=" * 70)
    print("TASK LIFECYCLE STATE/EVENT CONSISTENCY TEST")
    print("=" * 70)

    kernel = Kernel()

    received_events = []

    # --------------------------------------------------
    # EVENT HANDLER
    # --------------------------------------------------

    def handler(event):

        received_events.append(event)

        print(
            f"[DISPATCHER] "
            f"{event.event_type.value} "
            f"task={event.task_id}"
        )

    # --------------------------------------------------
    # SUBSCRIBE
    # --------------------------------------------------

    lifecycle_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_COMPLETED,
        KernelEventType.TASK_CANCELLED,
        KernelEventType.TASK_FAILED,
    ]

    for event_type in lifecycle_events:

        kernel.event_dispatcher.subscribe(
            event_type,
            handler
        )

    # ==================================================
    # CASE 1 — RUNNING → DONE
    # ==================================================

    done_task = kernel.start_task(
        "Complete a simple task."
    )

    kernel.complete_current_task()

    await asyncio.sleep(0.05)

    assert (
        done_task.status
        == TaskStatus.DONE
    )

    done_events = [
        event
        for event in received_events
        if event.task_id == done_task.task_id
    ]

    done_types = [
        event.event_type
        for event in done_events
    ]

    assert done_types == [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_COMPLETED,
    ]

    assert (
        done_events[-1].event_type
        == KernelEventType.TASK_COMPLETED
    )

    print("RUNNING → DONE              ✓")
    print("TASK_COMPLETED event        ✓")

    # ==================================================
    # CASE 2 — RUNNING → CANCELLED
    # ==================================================

    cancel_task = kernel.start_task(
        "Cancel this task."
    )

    kernel.cancel_current_task()

    await asyncio.sleep(0.05)

    assert (
        cancel_task.status
        == TaskStatus.CANCELLED
    )

    cancel_events = [
        event
        for event in received_events
        if event.task_id == cancel_task.task_id
    ]

    cancel_types = [
        event.event_type
        for event in cancel_events
    ]

    assert cancel_types == [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_CANCELLED,
    ]

    assert (
        cancel_events[-1].event_type
        == KernelEventType.TASK_CANCELLED
    )

    print("RUNNING → CANCELLED          ✓")
    print("TASK_CANCELLED event        ✓")

    # ==================================================
    # CASE 3 — RUNNING → FAILED
    # ==================================================

    failed_task = kernel.start_task(
        "Fail this task."
    )

    kernel.fail_current_task()

    await asyncio.sleep(0.05)

    assert (
        failed_task.status
        == TaskStatus.FAILED
    )

    failed_events = [
        event
        for event in received_events
        if event.task_id == failed_task.task_id
    ]

    failed_types = [
        event.event_type
        for event in failed_events
    ]

    assert failed_types == [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_FAILED,
    ]

    assert (
        failed_events[-1].event_type
        == KernelEventType.TASK_FAILED
    )

    print("RUNNING → FAILED             ✓")
    print("TASK_FAILED event            ✓")

    # ==================================================
    # VERIFY TASK ISOLATION
    # ==================================================

    assert (
        done_task.task_id
        != cancel_task.task_id
        != failed_task.task_id
    )

    assert all(
        event.task_id == done_task.task_id
        for event in done_events
    )

    assert all(
        event.task_id == cancel_task.task_id
        for event in cancel_events
    )

    assert all(
        event.task_id == failed_task.task_id
        for event in failed_events
    )

    print("Task ID isolation            ✓")

    # ==================================================
    # FINAL
    # ==================================================

    print()
    print("State/event consistency      ✓")
    print("Lifecycle ordering            ✓")
    print("Terminal event correctness    ✓")
    print()
    print(
        "TASK LIFECYCLE STATE/EVENT "
        "CONSISTENCY TEST PASSED"
    )


if __name__ == "__main__":
    asyncio.run(main())