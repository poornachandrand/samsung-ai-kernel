import asyncio

from gemini_kernel import GeminiKernelBridge
from livekit.agents import llm

from livekit_gemini_adapter import GeminiLiveKitLLM


async def main():
    bridge = GeminiKernelBridge()
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
        tools=[],
    )

    response = await stream.collect()

    print("TEXT:", response.text)
    print("TOOL CALLS:", response.tool_calls)

    if not response.tool_calls:
        raise RuntimeError(
            "LiveKit adapter did not produce a tool call."
        )

    tool_call = response.tool_calls[0]

    print("TOOL NAME:", tool_call.name)
    print("ARGUMENTS:", tool_call.arguments)

    if tool_call.name != "flight_search":
        raise RuntimeError(
            f"Unexpected tool: {tool_call.name}"
        )

    print("LIVEKIT GEMINI FUNCTION CALL PASSED")


if __name__ == "__main__":
    asyncio.run(main())
