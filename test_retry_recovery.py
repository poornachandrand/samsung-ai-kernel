import asyncio

from kernel import Kernel, TaskStatus
from kernel_events import KernelEventType


async def main():

    print("=" * 70)
    print("RETRY & RECOVERY REGRESSION TEST")
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

    task = kernel.start_task(
        "Search for a flight with temporary service failures."
    )

    result = await kernel.execute_tool(
        "flaky_flight_search",
        task.task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert result.success is True
    assert result.retryable is False
    assert result.data["attempt"] == 3

    print("Temporary failures recovered       ✓")
    print("Final tool result successful       ✓")
    print("Retry count reached 3              ✓")

    tool_started = [
        event
        for event in events
        if event.event_type == KernelEventType.TOOL_STARTED
    ]

    tool_failed = [
        event
        for event in events
        if event.event_type == KernelEventType.TOOL_FAILED
    ]

    tool_completed = [
        event
        for event in events
        if event.event_type == KernelEventType.TOOL_COMPLETED
    ]

    assert len(tool_started) == 3
    assert len(tool_failed) == 2
    assert len(tool_completed) == 1

    print("Three tool attempts recorded       ✓")
    print("Two retryable failures recorded    ✓")
    print("One final success recorded         ✓")

    assert all(
        event.task_id == task.task_id
        for event in events
    )

    assert task.status == TaskStatus.RUNNING

    print("Task ID consistency                ✓")
    print("Task remains valid after recovery  ✓")

    kernel.complete_current_task()

    assert task.status == TaskStatus.DONE

    print("Recovered task completed           ✓")
    print()
    print("RETRY & RECOVERY REGRESSION PASSED")


if __name__ == "__main__":
    asyncio.run(main())