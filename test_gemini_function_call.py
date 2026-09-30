import asyncio

from gemini_kernel import GeminiKernelBridge


async def main():
    bridge = GeminiKernelBridge()

    response, model = await bridge.generate(
        contents=(
            "I want to travel from Bengaluru to Delhi. "
            "Use the flight_search tool."
        ),
        config=bridge.tool_config,
    )

    print("MODEL:", model)
    print("TEXT:", response.text)
    print("FUNCTION CALLS:", response.function_calls)

    if not response.function_calls:
        raise RuntimeError("Gemini did not return a function call.")

    print("GEMINI FUNCTION CALL TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())
