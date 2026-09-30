import asyncio
import json

from google import genai

from kernel import Kernel
from extensions.smart_home import SmartHomeTool


SMART_HOME_FUNCTION = {
    "type": "function",
    "name": "smart_home",
    "description": "Control a smart home device.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "turn_on",
                    "turn_off",
                    "set_temperature",
                    "get_status"
                ]
            },
            "device": {
                "type": "string",
                "enum": [
                    "bedroom_light",
                    "living_room_light",
                    "bedroom_fan",
                    "living_room_fan",
                    "ac"
                ]
            },
            "temperature": {
                "type": "number"
            }
        },
        "required": ["action", "device"]
    }
}


async def execute_gemini_tool(
    kernel,
    task,
    arguments
):
    tool_arguments = {
        "action": arguments["action"],
        "device": arguments["device"]
    }

    if "temperature" in arguments:
        tool_arguments["temperature"] = arguments["temperature"]

    return await kernel.execute_tool(
        "smart_home",
        task.task_id,
        **tool_arguments
    )


def main():

    # Gemini client
    client = genai.Client(
        http_options={"api_version": "v1"}
    )

    # Kernel
    kernel = Kernel()

    # Smart Home tool
    smart_home = SmartHomeTool()
    kernel.register_tool(smart_home)

    # -------------------------
    # TASK A
    # -------------------------

    print("\n--- TASK A ---")

    task_a = kernel.start_task(
        "Turn on bedroom light"
    )

    print("Task A started.")

    # Ask Gemini
    interaction_a = client.interactions.create(
        model="gemini-3.6-flash",
        input="Turn on the bedroom light",
        tools=[SMART_HOME_FUNCTION]
    )

    function_call_a = None

    for step in interaction_a.steps:
        if step.type == "function_call":
            function_call_a = step
            break

    print("\nGemini Task A:")
    print("Function:", function_call_a.name)
    print("Arguments:", function_call_a.arguments)

    # -------------------------
    # USER INTERRUPTION
    # -------------------------

    print("\n--- USER INTERRUPTION ---")
    print(
        "User: Actually, turn on the living room light instead."
    )

    # Cancel Task A
    await_cancel = asyncio.run(
        kernel.cancel_current_task()
    )

    print("Task A cancelled.")

    # Try to execute the old Task A result
    print("\nSending old Task A result to Kernel...")

    result_a = asyncio.run(
        execute_gemini_tool(
            kernel,
            task_a,
            function_call_a.arguments
        )
    )

    print("Task A result:")
    print(result_a)

    # -------------------------
    # TASK B
    # -------------------------

    print("\n--- TASK B ---")

    task_b = kernel.start_task(
        "Turn on living room light"
    )

    print("Task B started.")

    # Ask Gemini about the new command
    interaction_b = client.interactions.create(
        model="gemini-3.6-flash",
        input="Actually, turn on the living room light instead.",
        tools=[SMART_HOME_FUNCTION]
    )

    function_call_b = None

    for step in interaction_b.steps:
        if step.type == "function_call":
            function_call_b = step
            break

    print("\nGemini Task B:")
    print("Function:", function_call_b.name)
    print("Arguments:", function_call_b.arguments)

    # Execute Task B
    result_b = asyncio.run(
        execute_gemini_tool(
            kernel,
            task_b,
            function_call_b.arguments
        )
    )

    print("\nTask B result:")
    print(result_b)

    # -------------------------
    # VERIFY
    # -------------------------

    assert result_b.success is True
    assert result_b.task_id == task_b.task_id
    assert result_b.tool_name == "smart_home"
    assert result_b.data["device"] == "living_room_light"
    assert result_b.data["action"] == "turn_on"

    print("\nGemini interruption test PASSED!")


if __name__ == "__main__":
    main()