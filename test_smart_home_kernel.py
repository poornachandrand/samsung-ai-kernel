import asyncio

from kernel import Kernel
from extensions.smart_home import SmartHomeTool


async def main():

    # 1. Create Kernel
    kernel = Kernel()

    # 2. Create SmartHomeTool
    smart_home = SmartHomeTool()

    # 3. Register SmartHomeTool with Kernel
    kernel.register_tool(smart_home)

    # 4. Start a Kernel task
    task = kernel.start_task(
        "Turn on bedroom light"
    )

    # 5. Execute SmartHomeTool through Kernel
    result = await kernel.execute_tool(
        "smart_home",
        task.task_id,
        action="turn_on",
        device="bedroom_light"
    )

    # 6. Print result
    print("\nTool result:")
    print(result)

    # 7. Verify
    assert result.success is True
    assert result.task_id == task.task_id
    assert result.tool_name == "smart_home"

    print("\nIntegration test PASSED!")


if __name__ == "__main__":
    asyncio.run(main())