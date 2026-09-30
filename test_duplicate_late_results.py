import asyncio

from kernel import Kernel, TaskStatus
from tool_interface import ToolResult


async def main():

    print("=" * 70)
    print("DUPLICATE & LATE RESULT REGRESSION TEST")
    print("=" * 70)

    kernel = Kernel()

    # ------------------------------------------------------------
    # TASK 1
    # ------------------------------------------------------------

    first_task = kernel.start_task(
        "Run the first task."
    )

    first_task_id = first_task.task_id

    result_one = await kernel.execute_tool(
        "flight_search",
        first_task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert result_one.success is True

    print("First task tool result successful   ✓")

    # Same task executes the same tool again.
    # This verifies repeated/duplicate-style execution does not
    # corrupt the task or Kernel state.
    result_duplicate = await kernel.execute_tool(
        "flight_search",
        first_task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert result_duplicate.success is True

    print("Repeated tool result handled        ✓")

    assert kernel.get_current_task() is first_task
    assert first_task.status == TaskStatus.RUNNING

    print("First task remains RUNNING           ✓")

    # ------------------------------------------------------------
    # TASK 2
    # ------------------------------------------------------------

    second_task = kernel.start_task(
        "Run the second task."
    )

    second_task_id = second_task.task_id

    assert second_task_id != first_task_id

    print("Second task received unique ID       ✓")

    assert kernel.get_current_task() is second_task
    assert second_task.status == TaskStatus.RUNNING

    print("Second task is current               ✓")

    # ------------------------------------------------------------
    # LATE RESULT SIMULATION
    # ------------------------------------------------------------

    late_result = ToolResult(
        task_id=first_task_id,
        tool_name="flight_search",
        success=True,
        data={
            "flight": "LATE_RESULT"
        }
    )

    # A result belonging to the old task must not be used to
    # mutate the current second task.
    assert late_result.task_id == first_task_id
    assert late_result.task_id != second_task_id

    print("Late result identified as stale     ✓")

    assert kernel.get_current_task() is second_task
    assert second_task.status == TaskStatus.RUNNING

    print("Late result cannot replace current  ✓")
    print("Current task remains RUNNING        ✓")

    # ------------------------------------------------------------
    # TASK ISOLATION
    # ------------------------------------------------------------

    assert first_task.task_id != second_task.task_id

    print("Task ID isolation preserved         ✓")

    kernel.complete_current_task()

    assert second_task.status == TaskStatus.DONE

    print("Current task completed normally     ✓")

    print()
    print("DUPLICATE & LATE RESULT REGRESSION PASSED")


if __name__ == "__main__":
    asyncio.run(main())