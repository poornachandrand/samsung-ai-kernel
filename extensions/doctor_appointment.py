from tool_base import BaseTool
from tool_interface import ToolResult


class DoctorAppointmentTool(BaseTool):

    @property
    def name(self):
        return "doctor_appointment"

    def __init__(self):
        self.appointments = []

    async def run(self, task_id: str, **kwargs):

        action = kwargs.get("action")

        # ====================================================
        # BOOK APPOINTMENT
        # ====================================================

        if action == "book_appointment":

            doctor = kwargs.get("doctor")
            date = kwargs.get("date")
            time = kwargs.get("time")

            if not doctor:
                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=False,
                    error="Doctor name is required.",
                    retryable=False
                )

            if not date:
                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=False,
                    error="Appointment date is required.",
                    retryable=False
                )

            if not time:
                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=False,
                    error="Appointment time is required.",
                    retryable=False
                )

            appointment = {
                "doctor": doctor,
                "date": date,
                "time": time,
                "status": "booked"
            }

            self.appointments.append(appointment)

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data={
                    "appointment": appointment,
                    "message": (
                        f"Appointment with Dr. {doctor} "
                        f"booked for {date} at {time}."
                    )
                },
                error=None,
                retryable=False
            )

        # ====================================================
        # CANCEL APPOINTMENT
        # ====================================================

        elif action == "cancel_appointment":

            if not self.appointments:
                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=False,
                    error="No active appointments to cancel.",
                    retryable=False
                )

            appointment = self.appointments.pop()

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data={
                    "cancelled_appointment": appointment,
                    "message": (
                        f"Appointment with Dr. "
                        f"{appointment['doctor']} cancelled."
                    )
                },
                error=None,
                retryable=False
            )

        # ====================================================
        # GET APPOINTMENTS
        # ====================================================

        elif action == "get_appointments":

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data={
                    "appointments": self.appointments,
                    "message": (
                        f"{len(self.appointments)} "
                        f"active appointment(s)."
                    )
                },
                error=None,
                retryable=False
            )

        # ====================================================
        # CLEAR APPOINTMENTS
        # ====================================================

        elif action == "clear_appointments":

            self.appointments.clear()

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data={
                    "appointments": [],
                    "message": "All appointments cleared."
                },
                error=None,
                retryable=False
            )

        # ====================================================
        # UNKNOWN ACTION
        # ====================================================

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=False,
            error=f"Unknown doctor appointment action: {action}",
            retryable=False
        )