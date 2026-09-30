import asyncio

from google import genai

from kernel import Kernel
from extensions.doctor_appointment import DoctorAppointmentTool
from interrupt_detector import InterruptDetector


DOCTOR_APPOINTMENT_FUNCTION = {
    "type": "function",
    "name": "doctor_appointment",
    "description": "Book, cancel, or view doctor appointments.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "book_appointment",
                    "cancel_appointment",
                    "get_appointments"
                ]
            },
            "doctor": {
                "type": "string"
            },
            "date": {
                "type": "string"
            },
            "time": {
                "type": "string"
            }
        },
        "required": ["action"]
    }
}


async def execute_doctor_tool(kernel, task, arguments):
    return await kernel.execute_tool(
        "doctor_appointment",
        task.task_id,
        **arguments
    )


def get_function_call(interaction):
    for step in interaction.steps:
        if step.type == "function_call":
            return step

    return None


def main():

    # --------------------------------------------------
    # Gemini
    # --------------------------------------------------

    client = genai.Client(
        http_options={"api_version": "v1"}
    )

    # --------------------------------------------------
    # Kernel
    # --------------------------------------------------

    kernel = Kernel()

    doctor_appointment = DoctorAppointmentTool()
    kernel.register_tool(doctor_appointment)

    # --------------------------------------------------
    # Interruption detector
    # --------------------------------------------------

    detector = InterruptDetector()

    # ==================================================
    # TASK A
    # ==================================================

    print("\n--- TASK A ---")

    original_request = (
        "Book an appointment with Dr Sharma tomorrow at 10 AM"
    )

    task_a = kernel.start_task(original_request)

    print("Task A started.")

    interaction_a = client.interactions.create(
        model="gemini-3.6-flash",
        input=original_request,
        tools=[DOCTOR_APPOINTMENT_FUNCTION]
    )

    function_call_a = get_function_call(interaction_a)

    print("\nGemini Task A:")
    print("Function:", function_call_a.name)
    print("Arguments:", function_call_a.arguments)

    # ==================================================
    # USER INTERRUPTION
    # ==================================================

    print("\n--- USER INTERRUPTION ---")

    interruption = "Make it 2 PM"

    print("User:", interruption)

    interruption_result = detector.classify_interruption(
        original_request,
        interruption
    )

    print("\nInterruption Detector:")
    print(interruption_result.to_dict())

    assert interruption_result.interrupted is True
    assert interruption_result.interruption_type == "correction"
    assert interruption_result.changed_slots["time"] == "2 PM"

    # ==================================================
    # CANCEL TASK A
    # ==================================================

    print("\nCancelling Task A...")

    asyncio.run(
        kernel.cancel_current_task()
    )

    print("Task A cancelled.")

    # ==================================================
    # TRY OLD TASK
    # ==================================================

    print("\nSending old Task A result to Kernel...")

    result_a = asyncio.run(
        execute_doctor_tool(
            kernel,
            task_a,
            function_call_a.arguments
        )
    )

    print("Task A result:")
    print(result_a)

    assert result_a.success is False

    # ==================================================
    # TASK B
    # ==================================================

    print("\n--- TASK B ---")

    corrected_request = (
        "Book an appointment with Dr Sharma tomorrow at 2 PM"
    )

    task_b = kernel.start_task(corrected_request)

    print("Task B started.")

    interaction_b = client.interactions.create(
        model="gemini-3.6-flash",
        input=corrected_request,
        tools=[DOCTOR_APPOINTMENT_FUNCTION]
    )

    function_call_b = get_function_call(interaction_b)

    print("\nGemini Task B:")
    print("Function:", function_call_b.name)
    print("Arguments:", function_call_b.arguments)

    # ==================================================
    # EXECUTE TASK B
    # ==================================================

    result_b = asyncio.run(
        execute_doctor_tool(
            kernel,
            task_b,
            function_call_b.arguments
        )
    )

    print("\nTask B result:")
    print(result_b)

    # ==================================================
    # VERIFY
    # ==================================================

    assert result_b.success is True
    assert result_b.task_id == task_b.task_id
    assert result_b.tool_name == "doctor_appointment"

    appointment = result_b.data["appointment"]

    assert appointment["doctor"] == "Dr Sharma"
    assert appointment["time"] == "2 PM"

    print("\nGemini Doctor Appointment interruption test PASSED!")


if __name__ == "__main__":
    main()