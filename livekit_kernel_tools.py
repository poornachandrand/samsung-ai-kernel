from livekit.agents import function_tool


class LiveKitKernelTools:

    def __init__(self, kernel):
        self.kernel = kernel

    # =========================================================
    # TASK MANAGEMENT
    # =========================================================

    def start_task(self, goal: str):
        task = self.kernel.start_task(goal)

        print(
            f"[KERNEL] LiveKit task started: "
            f"{task.task_id}"
        )

        return task

    async def _execute(
        self,
        tool_name: str,
        arguments: dict,
        goal: str,
    ):
        # Prevent Gemini Live from accidentally executing the exact same
        # state-changing function call twice within a short window.
        # This is intentionally local to this LiveKit bridge so the Kernel
        # architecture and direct Kernel execution remain unchanged.
        import asyncio
        import time

        if not hasattr(self, "_duplicate_guard_lock"):
            self._duplicate_guard_lock = asyncio.Lock()
            self._recent_calls = {}

        call_key = (
            tool_name,
            tuple(sorted(
                (str(key), repr(value))
                for key, value in arguments.items()
            )),
        )

        now = time.monotonic()

        async with self._duplicate_guard_lock:
            previous = self._recent_calls.get(call_key)

            if previous is not None:
                previous_time, previous_result = previous

                if now - previous_time < 3.0:
                    print(
                        f"[KERNEL] Duplicate LiveKit call suppressed: "
                        f"{tool_name}"
                    )
                    return previous_result

            self._recent_calls[call_key] = (now, None)

        task = self.start_task(goal)

        print(
            f"[KERNEL] Executing {tool_name} "
            f"for task {task.task_id}"
        )

        try:
            result = await self.kernel.execute_tool(
                tool_name=tool_name,
                task_id=task.task_id,
                **arguments,
            )

            # Convert ToolResult to JSON-safe data
            if hasattr(result, "to_dict"):
                result_dict = result.to_dict()

            elif hasattr(result, "__dict__"):
                result_dict = dict(result.__dict__)

            elif isinstance(result, dict):
                result_dict = result

            else:
                result_dict = {
                    "success": True,
                    "data": str(result),
                }

            # Convert nested ToolResult if present
            if isinstance(result_dict, dict):

                inner_data = result_dict.get("data")

                if hasattr(inner_data, "to_dict"):
                    result_dict["data"] = inner_data.to_dict()

                elif hasattr(inner_data, "__dict__"):
                    result_dict["data"] = dict(
                        inner_data.__dict__
                    )

                elif not isinstance(
                    inner_data,
                    (
                        dict,
                        list,
                        str,
                        int,
                        float,
                        bool,
                        type(None),
                    ),
                ):
                    result_dict["data"] = str(inner_data)

            print(
                f"[KERNEL] Result from {tool_name}: "
                f"{result_dict}"
            )

            async with self._duplicate_guard_lock:
                self._recent_calls[call_key] = (
                    time.monotonic(),
                    result_dict,
                )

            return result_dict

        except Exception as exc:

            async with self._duplicate_guard_lock:
                self._recent_calls.pop(call_key, None)

            print(
                f"[KERNEL] Exception while executing "
                f"{tool_name}: {exc}"
            )

            return {
                "success": False,
                "error": str(exc),
            }

    # =========================================================
    # SMART HOME
    # =========================================================

    @function_tool
    async def smart_home(
        self,
        device: str,
        action: str,
    ) -> dict:

        normalized_action = action.strip().lower()

        if normalized_action in (
            "on",
            "turnon",
            "turn on",
        ):
            normalized_action = "turn_on"

        elif normalized_action in (
            "off",
            "turnoff",
            "turn off",
        ):
            normalized_action = "turn_off"

        print(
            "[LIVEKIT] Smart home request: "
            f"device={device}, "
            f"action={action} -> {normalized_action}"
        )

        return await self._execute(
            tool_name="smart_home",
            arguments={
                "device": device,
                "action": normalized_action,
            },
            goal=(
                f"Control smart-home device "
                f"{device} with action "
                f"{normalized_action}"
            ),
        )

    # =========================================================
    # FLIGHT SEARCH
    # =========================================================

    @function_tool
    async def flight_search(
        self,
        origin: str,
        destination: str,
    ) -> dict:

        print(
            f"[LIVEKIT] Flight search: "
            f"{origin} -> {destination}"
        )

        return await self._execute(
            tool_name="flight_search",
            arguments={
                "origin": origin,
                "destination": destination,
            },
            goal=(
                f"Search flights from "
                f"{origin} to {destination}"
            ),
        )

    # =========================================================
    # HOTEL SEARCH
    # =========================================================

    @function_tool
    async def hotel_search(
        self,
        city: str,
    ) -> dict:

        print(
            f"[LIVEKIT] Hotel search: "
            f"city={city}"
        )

        return await self._execute(
            tool_name="hotel_search",
            arguments={
                "city": city,
            },
            goal=f"Search for hotels in {city}",
        )

    # =========================================================
    # DOCTOR APPOINTMENT
    # =========================================================

    @function_tool
    async def doctor_appointment(
        self,
        action: str,
        doctor: str = "",
        date: str = "",
        time: str = "",
    ) -> dict:

        normalized_action = action.strip().lower()

        if normalized_action in (
            "book",
            "book appointment",
            "book_appointment",
            "schedule",
            "schedule appointment",
        ):
            normalized_action = "book_appointment"

        elif normalized_action in (
            "cancel",
            "cancel appointment",
            "cancel_appointment",
        ):
            normalized_action = "cancel_appointment"

        elif normalized_action in (
            "get",
            "get appointments",
            "list",
            "list appointments",
            "get_appointments",
        ):
            normalized_action = "get_appointments"

        elif normalized_action in (
            "clear",
            "clear appointments",
            "clear_appointments",
        ):
            normalized_action = "clear_appointments"

        arguments = {
            "action": normalized_action,
        }

        if doctor:
            arguments["doctor"] = doctor

        if date:
            arguments["date"] = date

        if time:
            arguments["time"] = time

        print(
            "[LIVEKIT] Doctor appointment request: "
            f"{arguments}"
        )

        return await self._execute(
            tool_name="doctor_appointment",
            arguments=arguments,
            goal=(
                f"Manage doctor appointment "
                f"with action "
                f"{normalized_action}"
            ),
        )

    # =========================================================
    # KITCHEN ASSISTANT
    # =========================================================

    @function_tool
    async def kitchen_assistant(
        self,
        action: str,
        ingredient: str = "",
        quantity: str = "",
        recipe: str = "",
        ingredients: str = "",
    ) -> dict:

        normalized_action = action.strip().lower()

        aliases = {
            "add ingredient": "add_ingredient",
            "add": "add_ingredient",
            "remove ingredient": "remove_ingredient",
            "remove": "remove_ingredient",
            "check inventory": "check_inventory",
            "inventory": "check_inventory",
            "add recipe": "add_recipe",
            "recipe": "add_recipe",
            "get recipe": "get_recipe",
            "clear inventory": "clear_inventory",
            "clear": "clear_inventory",
        }

        normalized_action = aliases.get(
            normalized_action,
            normalized_action,
        )

        arguments = {
            "action": normalized_action,
        }

        if ingredient:
            arguments["ingredient"] = ingredient

        if quantity:
            arguments["quantity"] = quantity

        if recipe:
            arguments["recipe"] = recipe

        if ingredients:
            arguments["ingredients"] = ingredients

        print(
            "[LIVEKIT] Kitchen assistant request:"
            f"{arguments}"
        )

        return await self._execute(
            tool_name="kitchen_assistant",
            arguments=arguments,
            goal=(
                f"Manage kitchen request "
                f"with action {normalized_action}"
            ),
        )

    # =========================================================
    # STUDY HELPER
    # =========================================================

    @function_tool
    async def study_helper(
        self,
        action: str,
        subject: str = "",
        topic: str = "",
    ) -> dict:

        normalized_action = action.strip().lower()

        aliases = {
            "add topic": "add_topic",
            "add": "add_topic",
            "remove topic": "remove_topic",
            "remove": "remove_topic",
            "get topics": "get_topics",
            "topics": "get_topics",
            "list topics": "get_topics",
            "mark completed": "mark_completed",
            "complete": "mark_completed",
            "completed": "mark_completed",
            "clear subject": "clear_subject",
            "clear": "clear_subject",
        }

        normalized_action = aliases.get(
            normalized_action,
            normalized_action,
        )

        arguments = {
            "action": normalized_action,
        }

        if subject:
            arguments["subject"] = subject

        if topic:
            arguments["topic"] = topic

        print(
            "[LIVEKIT] Study helper request: "
            f"{arguments}"
        )

        return await self._execute(
            tool_name="study_helper",
            arguments=arguments,
            goal=(
                f"Manage study plan "
                f"with action {normalized_action}"
            ),
        )

    # =========================================================
    # EMPLOYEE PLANNER
    # =========================================================

    @function_tool
    async def employee_planner(
        self,
        action: str,
        employee: str = "",
        date: str = "",
        task: str = "",
        status: str = "",
    ) -> dict:

        normalized_action = action.strip().lower()

        aliases = {
            "add task": "add_task",
            "schedule task": "add_task",
            "schedule": "add_task",
            "remove task": "remove_task",
            "delete task": "remove_task",
            "remove": "remove_task",
            "get schedule": "get_schedule",
            "schedule for": "get_schedule",
            "view schedule": "get_schedule",
            "show schedule": "get_schedule",
            "update status": "update_status",
            "mark completed": "update_status",
            "complete": "update_status",
        }

        normalized_action = aliases.get(
            normalized_action,
            normalized_action,
        )

        arguments = {
            "action": normalized_action,
        }

        if employee:
            arguments["employee"] = employee

        if date:
            arguments["date"] = date

        if task:
            arguments["task"] = task

        if status:
            arguments["status"] = status

        print(
            "[LIVEKIT] Employee planner request: "
            f"{arguments}"
        )

        return await self._execute(
            tool_name="employee_planner",
            arguments=arguments,
            goal=(
                f"Manage employee schedule "
                f"with action {normalized_action}"
            ),
        )

    # =========================================================
    # ALL LIVEKIT TOOLS
    # =========================================================

    def get_tools(self):
        return [
            self.smart_home,
            self.flight_search,
            self.hotel_search,
            self.doctor_appointment,
            self.kitchen_assistant,
            self.study_helper,
            self.employee_planner,
        ]
