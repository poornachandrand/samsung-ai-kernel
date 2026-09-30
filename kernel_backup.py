from tool_base import BaseTool
from tool_interface import ToolResult

from extensions.doctor_appointment import DoctorAppointmentTool
from extensions.employee_planner import EmployeePlannerTool
from extensions.food_ordering import FoodOrderingTool
from extensions.kitchen_assistant import KitchenAssistantTool
from extensions.smart_home import SmartHomeTool
from extensions.study_helper import StudyHelperTool

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import uuid
import json


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Task:
    task_id: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING

    current_step: int = 0
    checkpoint: dict[str, Any] = field(default_factory=dict)

    # Keep compatibility with the original flight tests
    slots: dict[str, Any] = field(default_factory=dict)

    retry_count: int = 0


def create_task(
    goal: str,
    slots: dict[str, Any] | None = None
) -> Task:

    if slots is None:
        slots = {}

    return Task(
        task_id=str(uuid.uuid4()),
        goal=goal,
        slots=slots.copy(),
        checkpoint=slots.copy()
    )


class Kernel:

    def __init__(self):

        self.current_task = None
        self.current_task_id = None

        # Actual asyncio task
        self._current_async_task = None

        # Tool registry
        self.tools = {}

        # Register extension tools
        self.register_tool(DoctorAppointmentTool())
        self.register_tool(EmployeePlannerTool())
        self.register_tool(FoodOrderingTool())
        self.register_tool(KitchenAssistantTool())
        self.register_tool(SmartHomeTool())
        self.register_tool(StudyHelperTool())

        self.processed_results = set()
        self.max_retries = 3

        # Stores latest user input
        self.last_user_input = None

    # ========================================================
    # TOOL REGISTRATION
    # ========================================================

    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool
        print(f"Tool registered: {tool.name}")

    # ========================================================
    # EXECUTE TOOL
    # ========================================================

    async def execute_tool(
        self,
        tool_name: str,
        task_id: str,
        **kwargs: Any
    ) -> ToolResult:

        if self.current_task is None:
            return ToolResult(
                task_id=task_id,
                tool_name=tool_name,
                success=False,
                error="No current task.",
                retryable=False
            )

        if task_id != self.current_task_id:
            return ToolResult(
                task_id=task_id,
                tool_name=tool_name,
                success=False,
                error="Ignoring tool result from old task.",
                retryable=False
            )

        if tool_name not in self.tools:
            return ToolResult(
                task_id=task_id,
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' is not registered.",
                retryable=False
            )

        tool = self.tools[tool_name]

        try:
            result = await tool.run(
                task_id,
                **kwargs
            )

            return result

        except Exception as e:
            return ToolResult(
                task_id=task_id,
                tool_name=tool_name,
                success=False,
                error=str(e),
                retryable=True
            )

    # ========================================================
    # START TASK
    # ========================================================

    def start_task(
        self,
        goal: str,
        slots: dict[str, Any] | None = None
    ):
        task = create_task(goal, slots)

        task.status = TaskStatus.RUNNING

        self.current_task = task
        self.current_task_id = task.task_id

        print(f"Started task: {task.task_id}")
        print(f"Goal: {task.goal}")

        return task

    # ========================================================
    # HANDLE USER INPUT
    # ========================================================

    def handle_user_input(self, user_input: str):
        self.last_user_input = user_input

        print(f"User input received: {user_input}")

        return user_input

    # ========================================================
    # HANDLE USER CORRECTION
    # ========================================================

    def handle_user_correction(self, correction: str):

        print(f"User correction received: {correction}")

        # Cancel currently running asyncio task
        if self._current_async_task is not None:

            if not self._current_async_task.done():

                self._current_async_task.cancel()

            self._current_async_task = None

        # Cancel current kernel task
        if self.current_task is not None:

            self.current_task.status = TaskStatus.CANCELLED

        old_task_id = self.current_task_id

        print(f"Cancelled task: {old_task_id}")

        # Create a new corrected task
        new_task = create_task(
            correction,
            slots={}
        )

        new_task.status = TaskStatus.RUNNING

        self.current_task = new_task
        self.current_task_id = new_task.task_id

        print(f"Started corrected task: {new_task.task_id}")
        print(f"Corrected goal: {new_task.goal}")

        return new_task

    # ========================================================
    # CANCEL CURRENT TASK
    # ========================================================

    def cancel_current_task(self):

        if self._current_async_task is not None:

            if not self._current_async_task.done():
                self._current_async_task.cancel()

            self._current_async_task = None

        if self.current_task is not None:

            self.current_task.status = TaskStatus.CANCELLED

            print(
                f"Task cancelled: "
                f"{self.current_task.task_id}"
            )

        self.current_task = None
        self.current_task_id = None

    # ========================================================
    # COMPLETE CURRENT TASK
    # ========================================================

    def complete_current_task(self):

        if self.current_task is None:
            return

        self.current_task.status = TaskStatus.DONE

        print(
            f"Task completed: "
            f"{self.current_task.task_id}"
        )

    # ========================================================
    # FAIL CURRENT TASK
    # ========================================================

    def fail_current_task(self):

        if self.current_task is None:
            return

        self.current_task.status = TaskStatus.FAILED

        print(
            f"Task failed: "
            f"{self.current_task.task_id}"
        )

    # ========================================================
    # CHECK CURRENT TASK
    # ========================================================

    def get_current_task(self):

        return self.current_task

    # ========================================================
    # GET REGISTERED TOOLS
    # ========================================================

    def get_registered_tools(self):

        return list(self.tools.keys())
