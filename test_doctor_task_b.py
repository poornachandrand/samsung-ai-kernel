import asyncio
from kernel import Kernel
from extensions.doctor_appointment import DoctorAppointmentTool


async def main():
    kernel = Kernel()

    doctor_appointment = DoctorAppointmentTool()
    kernel.register_tool(doctor_appointment)

    print("\n--- TASK B ---")

    request = "Book an appointment with Dr Sharma tomorrow at 2 PM"

    task_b = kernel.start_task(request)

    print("Task B started.")
    print("Executing corrected appointment...")

    result_b = await kernel.execute_tool(
        "doctor_appointment",
        task_b.task_id,
        action="book_appointment",
        doctor="Dr Sharma",
        date="tomorrow",
        time="2 PM"
    )

    print("\nTask B result:")
    print(result_b)

    assert result_b.success is True
    assert result_b.task_id == task_b.task_id
    assert result_b.tool_name == "doctor_appointment"

    appointment = result_b.data["appointment"]

    assert appointment["doctor"] == "Dr Sharma"
    assert appointment["date"] == "tomorrow"
    assert appointment["time"] == "2 PM"

    print("\nDoctor Appointment corrected Task B PASSED!")


if __name__ == "__main__":
    asyncio.run(main())