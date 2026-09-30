import asyncio

from kernel import Kernel
from livekit.agents import AgentSession

from livekit_kernel_tools import LiveKitKernelTools


async def main():
    kernel = Kernel()
    kernel_tools = LiveKitKernelTools(kernel)

    tools = kernel_tools.get_tools()

    print("TOOLS:")
    for tool in tools:
        print(" -", tool.id)

    session = AgentSession(
        tools=tools,
    )

    print("AGENT SESSION TOOL INTEGRATION PASSED")


if __name__ == "__main__":
    asyncio.run(main())
