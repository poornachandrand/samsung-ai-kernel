import asyncio

from kernel import Kernel, TaskStatus
from kernel_events import KernelEventType


async def main():

    print("=" * 70)
    print("MULTI-TOOL INTEGRATION & FAILURE ISOLATION TEST")
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
    # MULTIPLE SUCCESSFUL TOOLS
    # ------------------------------------------------------------

    task = kernel.start_task(
        "Search for a flight and a hotel."
    )

    results = await kernel.execute_multiple_tools(
        task.task_id,
        [
            {
                "tool_name": "flight_search",
                "arguments": {
                    "origin": "Bengaluru",
                    "destination": "Delhi"
                }
            },
            {
                "tool_name": "hotel_search",
                "arguments": {
                    "city": "Delhi"
                }
            }
        ]
    )

    assert "flight_search" in results
    assert "hotel_search" in results

    assert results["flight_search"].success is True
    assert results["hotel_search"].success is True

    print("Flight tool succeeded               ✓")
    print("Hotel tool succeeded                ✓")
    print("Multiple tools executed             ✓")

    # ------------------------------------------------------------
    # VERIFY EVENTS
    # ------------------------------------------------------------

    completed_tools = [
        event
        for event in events
        if event.event_type == KernelEventType.TOOL_COMPLETED
    ]

    assert len(completed_tools) == 2

    completed_names = {
        event.tool_name
        for event in completed_tools
    }

    assert completed_names == {
        "flight_search",
        "hotel_search"
    }

    print("Both tool completion events recorded ✓")

    # ------------------------------------------------------------
    # FAILURE ISOLATION
    # ------------------------------------------------------------

    failure_task = kernel.start_task(
        "Run one invalid tool request and one valid tool request."
    )

    failure_results = await kernel.execute_multiple_tools(
        failure_task.task_id,
        [
            {
                "tool_name": "smart_home",
                "arguments": {
                    "action": "invalid_action",
                    "device": "living_room_light"
                }
            },
            {
                "tool_name": "hotel_search",
                "arguments": {
                    "city": "Mumbai"
                }
            }
        ]
    )

    assert "smart_home" in failure_results
    assert "hotel_search" in failure_results

    assert failure_results["smart_home"].success is False
    assert failure_results["hotel_search"].success is True

    print("Expected tool failure recorded      ✓")
    print("Independent tool still succeeded    ✓")
    print("Failure isolation preserved          ✓")

    # ------------------------------------------------------------
    # TASK STATE
    # ------------------------------------------------------------

    assert kernel.get_current_task() is failure_task
    assert failure_task.status == TaskStatus.RUNNING

    print("Task remains valid after failure     ✓")

    kernel.complete_current_task()

    assert failure_task.status == TaskStatus.DONE

    print("Task completed normally              ✓")

    print()
    print("MULTI-TOOL INTEGRATION &")
    print("FAILURE ISOLATION TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())