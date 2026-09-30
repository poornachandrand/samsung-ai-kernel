import asyncio

from kernel import Kernel
from extensions.smart_home import SmartHomeTool


async def main():

    # -------------------------
    # CREATE KERNEL
    # -------------------------
    kernel = Kernel()

    # -------------------------
    # REGISTER SMART HOME TOOL
    # -------------------------
    smart_home = SmartHomeTool()
    kernel.register_tool(smart_home)

    # -------------------------
    # TASK A
    # -------------------------
    print("\n--- TASK A ---")

    task_a = kernel.start_task(
        "Turn on bedroom light"
    )

    print("Task A started.")

    # Start SmartHomeTool for Task A
    task_a_tool = asyncio.create_task(
        kernel.execute_tool(
            "smart_home",
            task_a.task_id,
            action="turn_on",
            device="bedroom_light"
        )
    )

    # Give Task A a moment to start
    await asyncio.sleep(0.1)

    # -------------------------
    # USER INTERRUPTION
    # -------------------------
    print("\n--- USER INTERRUPTION ---")

    print(
        "User: Wait, turn on living room light instead."
    )

    # Cancel Task A
    await kernel.cancel_current_task()

    # -------------------------
    # LATE RESULT FROM TASK A
    # -------------------------
    try:

        result_a = await task_a_tool

        print("\nLate result from Task A:")
        print(result_a)

        # Simulate the late result reaching Kernel
        print("\nSending late result to Kernel...")

        kernel.complete_task(
            result_a.task_id,
            f"result-{result_a.task_id}"
        )

    except asyncio.CancelledError:

        print(
            "Task A tool call was cancelled."
        )

    # -------------------------
    # TASK B
    # -------------------------
    print("\n--- TASK B ---")

    task_b = kernel.start_task(
        "Turn on living room light"
    )

    print("Task B started.")

    result_b = await kernel.execute_tool(
        "smart_home",
        task_b.task_id,
        action="turn_on",
        device="living_room_light"
    )

    print("\nTask B result:")
    print(result_b)

    # -------------------------
    # VERIFY TASK B
    # -------------------------
    assert result_b.success is True

    assert result_b.task_id == task_b.task_id

    assert result_b.tool_name == "smart_home"

    assert result_b.data["device"] == "living_room_light"

    assert result_b.data["action"] == "turn_on"

    print("\nInterruption test PASSED!")


if __name__ == "__main__":
    asyncio.run(main())