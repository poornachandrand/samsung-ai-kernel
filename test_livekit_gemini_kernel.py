import asyncio
import json

from gemini_kernel import GeminiKernelBridge
from livekit.agents import llm

from livekit_gemini_adapter import GeminiLiveKitLLM
from livekit_kernel_tools import LiveKitKernelTools
from kernel import Kernel


async def main():
    bridge = GeminiKernelBridge()

    kernel = Kernel()
    kernel_tools = LiveKitKernelTools(kernel)

    task_id = kernel_tools.start_task(
        "Search for a flight from Bengaluru to Delhi."
    )

    livekit_llm = GeminiLiveKitLLM(bridge)

    chat_ctx = llm.ChatContext()
    chat_ctx.add_message(
        role="user",
        content=(
            "I want to travel from Bengaluru to Delhi. "
            "Search for a flight."
        ),
    )

    stream = livekit_llm.chat(
        chat_ctx=chat_ctx,
        tools=kernel_tools.get_tools(),
    )

    response = await stream.collect()

    print("GEMINI TOOL CALLS:", response.tool_calls)

    if not response.tool_calls:
        raise RuntimeError("No Gemini tool call received.")

    tool_call = response.tool_calls[0]

    print("TOOL:", tool_call.name)
    print("ARGUMENTS:", tool_call.arguments)

    arguments = json.loads(tool_call.arguments)

    result = await kernel.execute_tool(
        tool_call.name,
        task_id,
        **arguments,
    )

    print("KERNEL RESULT:")
    print(result)

    if not result.success:
        raise RuntimeError(
            f"Kernel tool execution failed: {result.error}"
        )

    print()
    print("=" * 60)
    print("LIVEKIT -> GEMINI -> KERNEL -> TOOL PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
