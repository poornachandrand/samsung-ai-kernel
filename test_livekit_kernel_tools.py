import asyncio

from kernel import Kernel
from livekit_kernel_tools import LiveKitKernelTools


async def main():
    kernel = Kernel()
    tools = LiveKitKernelTools(kernel)

    task_id = tools.start_task(
        "Test the smart home tool through the LiveKit Kernel bridge."
    )

    print("TASK ID:", task_id)

    result = await tools.smart_home(
        device="living_room_light",
        action="turn_on",
    )

    print("TOOL RESULT:")
    print(result)

    if task_id not in result:
        raise RuntimeError("Kernel task ID missing from tool result.")

    if '"success": true' not in result.lower():
        raise RuntimeError("Smart home tool did not report success.")

    print("LIVEKIT KERNEL TOOL EXECUTION PASSED")


if __name__ == "__main__":
    asyncio.run(main())
