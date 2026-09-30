import asyncio
from gemini_kernel import GeminiKernelBridge

async def main():
    bridge = GeminiKernelBridge()

    print("Testing Gemini directly...")
    response, model = await bridge.generate(
        contents="Reply with exactly: GEMINI TEST OK",
        config=bridge.tool_config,
    )

    print("MODEL:", model)
    print("RESPONSE:", response.text)

if __name__ == "__main__":
    asyncio.run(main())
