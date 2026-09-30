import asyncio

from gemini_kernel import GeminiKernelBridge
from livekit.agents import llm

from livekit_gemini_adapter import GeminiLiveKitLLM


async def main():
    bridge = GeminiKernelBridge()
    adapter = GeminiLiveKitLLM(bridge)

    chat_ctx = llm.ChatContext()

    chat_ctx.add_message(
        role="user",
        content="Say exactly: Samsung AI Kernel adapter test successful."
    )

    stream = adapter.chat(
        chat_ctx=chat_ctx,
        tools=[],
    )

    response_text = ""

    async with stream:
        async for chunk in stream:
            if chunk.delta and chunk.delta.content:
                response_text += chunk.delta.content

    print("ADAPTER RESPONSE:")
    print(response_text)

    if not response_text.strip():
        raise RuntimeError("Adapter returned an empty response.")

    print("LIVEKIT GEMINI ADAPTER TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())