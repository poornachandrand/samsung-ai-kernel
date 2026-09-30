import asyncio

from gemini_kernel import GeminiKernelBridge
from kernel import TaskStatus


async def main():
    print("=" * 70)
    print("GEMINI CANCELLATION TEST")
    print("=" * 70)

    bridge = GeminiKernelBridge()
    kernel = bridge.kernel

    # Start a Gemini-related Kernel task.
    task = kernel.start_task(
        "Plan a trip from Bengaluru to Delhi"
    )

    task_id = task.task_id

    assert kernel.get_task_status() == TaskStatus.RUNNING
    print("Task started                         ✓")

    # Cancel the active task.
    kernel.cancel_current_task()

    assert task.status == TaskStatus.CANCELLED
    print("Task cancelled                       ✓")

    assert kernel.get_task_status() == TaskStatus.CANCELLED
    print("Terminal CANCELLED state preserved   ✓")

    # Verify cancellation does not accidentally
    # create or switch to another task.
    assert kernel.get_current_task().task_id == task_id
    print("Cancelled task remains current       ✓")

    print()
    print("=" * 70)
    print("GEMINI CANCELLATION TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())