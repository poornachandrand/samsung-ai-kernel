import asyncio

from gemini_kernel import GeminiKernelBridge


async def main():

    print("=" * 70)
    print("GEMINI RECOVERY & FALLBACK TEST")
    print("=" * 70)

    bridge = GeminiKernelBridge()

    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": "Reply with exactly: Gemini recovery test passed."
                }
            ]
        }
    ]

    response, model_name = await bridge.generate(contents)

    assert response is not None
    print("Gemini returned a response            ✓")

    assert model_name is not None
    assert len(model_name.strip()) > 0
    print("Successful model identified           ✓")
    print(f"Model used: {model_name}")

    response_text = response.candidates[0].content.parts[0].text

    assert response_text is not None
    assert len(response_text.strip()) > 0
    print("Response contains text                ✓")

    print()
    print("Gemini response:")
    print(response_text)

    print()
    print("GEMINI RECOVERY & FALLBACK TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())