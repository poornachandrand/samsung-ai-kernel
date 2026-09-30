import asyncio

from kernel import Kernel, TaskStatus
from kernel_events import KernelEventType


async def main():

    print("=" * 70)
    print("END-TO-END LOCAL KERNEL INTEGRATION TEST")
    print("=" * 70)

    kernel = Kernel()

    events = []

    def handler(event):
        events.append(event)
        print(
            f"[EVENT] "
            f"{event.event_type.value} "
            f"task={event.task_id} "
            f"tool={event.tool_name}"
        )

    kernel.event_stream.subscribe(handler)

    # ------------------------------------------------------------
    # START TASK
    # ------------------------------------------------------------

    task = kernel.start_task(
        "Plan a Bengaluru to Delhi trip with a flight and hotel."
    )

    task_id = task.task_id

    assert task.status == TaskStatus.RUNNING

    print("Task started                         ✓")

    # ------------------------------------------------------------
    # FLIGHT SEARCH WITH AUTOMATIC RETRY
    # ------------------------------------------------------------

    flight_result = await kernel.execute_tool(
        "flaky_flight_search",
        task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert flight_result.success is True
    assert flight_result.data["attempt"] == 3

    print("Flight search recovered after retry ✓")

    kernel.save_checkpoint(
        "flight_search_complete",
        "flight_search",
        flight=flight_result.data
    )

    print("Flight checkpoint saved             ✓")

    # ------------------------------------------------------------
    # HOTEL SEARCH
    # ------------------------------------------------------------

    hotel_result = await kernel.execute_tool(
        "hotel_search",
        task_id,
        city="Delhi"
    )

    assert hotel_result.success is True

    print("Hotel search succeeded               ✓")

    kernel.save_checkpoint(
        "hotel_search_complete",
        "hotel_search",
        hotel=hotel_result.data
    )

    print("Hotel checkpoint saved              ✓")

    # ------------------------------------------------------------
    # VERIFY EVENT FLOW
    # ------------------------------------------------------------

    event_types = [
        event.event_type
        for event in events
    ]

    assert KernelEventType.TASK_STARTED in event_types
    assert KernelEventType.TOOL_STARTED in event_types
    assert KernelEventType.TOOL_FAILED in event_types
    assert KernelEventType.TOOL_COMPLETED in event_types
    assert KernelEventType.CHECKPOINT_SAVED in event_types

    print("Task/tool/checkpoint events present ✓")

    tool_failed_count = sum(
        event.event_type == KernelEventType.TOOL_FAILED
        for event in events
    )

    tool_completed_count = sum(
        event.event_type == KernelEventType.TOOL_COMPLETED
        for event in events
    )

    checkpoint_count = sum(
        event.event_type == KernelEventType.CHECKPOINT_SAVED
        for event in events
    )

    assert tool_failed_count == 2
    assert tool_completed_count == 2
    assert checkpoint_count == 2

    print("Retry failure events correct        ✓")
    print("Tool completion events correct     ✓")
    print("Checkpoint events correct          ✓")

    # ------------------------------------------------------------
    # COMPLETE TASK
    # ------------------------------------------------------------

    kernel.complete_current_task()

    assert task.status == TaskStatus.DONE

    print("Task completed                      ✓")

    assert events[-1].event_type == KernelEventType.TASK_COMPLETED
    assert events[-1].task_id == task_id

    print("Final TASK_COMPLETED event correct  ✓")

    # ------------------------------------------------------------
    # FINAL TASK ISOLATION
    # ------------------------------------------------------------

    assert all(
        event.task_id == task_id
        for event in events
    )

    print("All events belong to same task      ✓")

    print()
    print("END-TO-END LOCAL KERNEL")
    print("INTEGRATION TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())