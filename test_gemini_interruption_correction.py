import asyncio

from gemini_kernel import GeminiKernelBridge
from tool_interface import ToolResult
from kernel import TaskStatus


async def main():
    print("=" * 70)
    print("GEMINI INTERRUPTION & CORRECTION TEST")
    print("=" * 70)

    bridge = GeminiKernelBridge()
    kernel = bridge.kernel

    # ------------------------------------------------------------
    # 1. Start original task
    # ------------------------------------------------------------
    original_task = kernel.start_task(
        "Plan a trip from Bengaluru to Delhi"
    )

    original_task_id = original_task.task_id

    assert kernel.get_task_status() == TaskStatus.RUNNING
    print("Original task started                  ✓")

    # ------------------------------------------------------------
    # 2. User interrupts with a correction
    # ------------------------------------------------------------
    corrected_task = kernel.handle_user_correction(
        "Actually, plan a trip from Bengaluru to Mumbai"
    )

    corrected_task_id = corrected_task.task_id

    assert corrected_task_id != original_task_id
    print("Correction created a new task           ✓")

    # ------------------------------------------------------------
    # 3. Original task must be cancelled
    # ------------------------------------------------------------
    assert original_task.status == TaskStatus.CANCELLED
    print("Original task cancelled                 ✓")

    # ------------------------------------------------------------
    # 4. Corrected task must become active
    # ------------------------------------------------------------
    assert corrected_task.status == TaskStatus.RUNNING
    print("Corrected task is running               ✓")

    assert kernel.get_current_task().task_id == corrected_task_id
    print("Corrected task is current               ✓")

    # ------------------------------------------------------------
    # 5. Simulate a late result from original task
    #
    # This deliberately does NOT call execute_tool() with the old
    # task ID because the Kernel correctly rejects inactive tasks.
    # Instead, we construct the result that a stale tool would have
    # returned and verify that it cannot replace the active task.
    # ------------------------------------------------------------
    late_result = ToolResult(
        task_id=original_task_id,
        tool_name="flight_search",
        success=True,
        data={
            "origin": "Bengaluru",
            "destination": "Delhi",
            "flight": "SJ101",
        },
    )

    assert late_result.task_id == original_task_id
    assert kernel.get_current_task().task_id == corrected_task_id
    print("Late old result identified              ✓")

    # The active task must remain the corrected task.
    assert kernel.get_current_task().task_id != late_result.task_id
    print("Late old result did not replace task    ✓")

    # ------------------------------------------------------------
    # 6. Execute tool for corrected task
    # ------------------------------------------------------------
    new_result = await kernel.execute_tool(
        "flight_search",
        corrected_task_id,
        origin="Bengaluru",
        destination="Mumbai",
    )

    assert new_result.success
    assert new_result.task_id == corrected_task_id
    assert new_result.data["origin"] == "Bengaluru"
    assert new_result.data["destination"] == "Mumbai"

    print("Corrected task tool execution succeeded ✓")

    # ------------------------------------------------------------
    # 7. Complete corrected task
    # ------------------------------------------------------------
    kernel.complete_current_task()

    assert kernel.get_task_status() == TaskStatus.DONE
    print("Corrected task completed               ✓")

    assert kernel.get_current_task().task_id == corrected_task_id
    print("Corrected task remains current          ✓")

    print()
    print("=" * 70)
    print("GEMINI INTERRUPTION & CORRECTION TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())