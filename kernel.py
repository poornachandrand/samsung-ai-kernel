import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from tool_base import BaseTool
from tool_interface import ToolResult

from tools import (
    SmartHomeTool,
    FlightSearchTool,
    FlakyFlightSearchTool,
    HotelSearchTool,
)

from extensions.doctor_appointment import (
    DoctorAppointmentTool,
)

from extensions.kitchen_assistant import (
    KitchenAssistantTool,
)

from extensions.study_helper import (
    StudyHelperTool,
)

from extensions.employee_planner import (
    EmployeePlannerTool,
)

from kernel_events import (
    EventStream,
    KernelEventType,
    create_event,
)

from event_dispatcher import EventDispatcher


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

    checkpoint: str | None = None

    slots: dict[str, Any] = field(
        default_factory=dict
    )

    retry_count: int = 0

    results: dict[str, ToolResult] = field(
        default_factory=dict
    )

    completed_steps: list[str] = field(
        default_factory=list
    )


class Kernel:

    def __init__(self):

        self.current_task: Task | None = None

        self.current_task_id: str | None = None

        self._current_async_task: (
            asyncio.Task | None
        ) = None

        self.tools: dict[str, BaseTool] = {}

        self.max_retries = 3

        # --------------------------------------------------
        # EVENT SYSTEM
        # --------------------------------------------------

        self.event_stream = EventStream()

        self.event_dispatcher = EventDispatcher(
            self.event_stream
        )

        self.event_dispatcher.attach()

        # --------------------------------------------------
        # CORE TOOLS
        # --------------------------------------------------

        self.register_tool(
            SmartHomeTool()
        )

        self.register_tool(
            FlightSearchTool()
        )

        self.register_tool(
            FlakyFlightSearchTool()
        )

        self.register_tool(
            HotelSearchTool()
        )

        self.register_tool(
            DoctorAppointmentTool()
        )

        # --------------------------------------------------
        # EXTENSION TOOLS
        # --------------------------------------------------

        self.register_tool(
            KitchenAssistantTool()
        )

        self.register_tool(
            StudyHelperTool()
        )

        self.register_tool(
            EmployeePlannerTool()
        )

    # ======================================================
    # EVENT EMISSION
    # ======================================================

    def emit_event(
        self,
        event_type: KernelEventType,
        task_id: str,
        tool_name: str | None = None,
        step_name: str | None = None,
        checkpoint: str | None = None,
        data: Any = None,
        error: str | None = None,
    ) -> None:

        event = create_event(
            event_type=event_type,
            task_id=task_id,
            tool_name=tool_name,
            step_name=step_name,
            checkpoint=checkpoint,
            data=data,
            error=error,
        )

        self.event_stream.emit(event)

    # ======================================================
    # TOOL REGISTRY
    # ======================================================

    def register_tool(
        self,
        tool: BaseTool
    ) -> None:

        self.tools[tool.name] = tool

        print(
            f"Tool registered: {tool.name}"
        )

    # ======================================================
    # CREATE / START TASK
    # ======================================================

    def start_task(
        self,
        goal: str
    ) -> Task:

        task = Task(
            task_id=str(uuid.uuid4()),
            goal=goal,
            status=TaskStatus.RUNNING,
        )

        self.current_task = task
        self.current_task_id = task.task_id

        self.emit_event(
            KernelEventType.TASK_STARTED,
            task_id=task.task_id,
            data={
                "goal": goal
            },
        )

        print(
            f"Started task: {task.task_id}"
        )

        print(
            f"Goal: {goal}"
        )

        return task

    # ======================================================
    # EXECUTE TOOL
    # ======================================================

    async def execute_tool(
        self,
        tool_name: str,
        task_id: str,
        **kwargs: Any,
    ) -> ToolResult:

        # --------------------------------------------------
        # VALIDATE ACTIVE TASK
        # --------------------------------------------------

        if self.current_task is None:
            raise RuntimeError(
                "No active Kernel task. "
                "Start a task before executing a tool."
            )

        if self.current_task_id != task_id:
            raise RuntimeError(
                f"Task mismatch. "
                f"Active task: {self.current_task_id}, "
                f"requested task: {task_id}"
            )

        task = self.current_task

        # --------------------------------------------------
        # VALIDATE TASK STATUS
        # --------------------------------------------------

        if task.status != TaskStatus.RUNNING:
            raise RuntimeError(
                f"Task {task_id} is not running. "
                f"Current status: {task.status.value}"
            )

        # --------------------------------------------------
        # VALIDATE TOOL
        # --------------------------------------------------

        if tool_name not in self.tools:

            result = ToolResult(
                task_id=task_id,
                tool_name=tool_name,
                success=False,
                error=(
                    f"Unknown tool: {tool_name}"
                ),
                retryable=False,
            )

            task.results[tool_name] = result

            self.emit_event(
                KernelEventType.TOOL_FAILED,
                task_id=task_id,
                tool_name=tool_name,
                error=result.error,
            )

            return result

        tool = self.tools[tool_name]

        # --------------------------------------------------
        # TOOL START
        # --------------------------------------------------

        self.emit_event(
            KernelEventType.TOOL_STARTED,
            task_id=task_id,
            tool_name=tool_name,
            data=kwargs,
        )

        print(
            f"Executing tool: {tool_name}"
        )

        print(
            f"Arguments: {kwargs}"
        )

        # --------------------------------------------------
        # RETRY LOOP
        # --------------------------------------------------

        last_result: ToolResult | None = None

        for attempt in range(
            1,
            self.max_retries + 1
        ):

            task.retry_count = attempt - 1

            try:

                print(
                    f"Attempt {attempt}: "
                    f"{tool_name}"
                )

                result = await tool.run(
                    task_id,
                    **kwargs,
                )

                last_result = result

                # --------------------------------------------------
                # SUCCESS
                # --------------------------------------------------

                if result.success:

                    task.results[
                        tool_name
                    ] = result

                    task.completed_steps.append(
                        tool_name
                    )

                    self.emit_event(
                        KernelEventType.TOOL_COMPLETED,
                        task_id=task_id,
                        tool_name=tool_name,
                        data=result.data,
                    )

                    print(
                        f"'{tool_name}' "
                        f"succeeded on attempt {attempt}."
                    )

                    return result

                # --------------------------------------------------
                # NON-RETRYABLE FAILURE
                # --------------------------------------------------

                if not result.retryable:

                    task.results[
                        tool_name
                    ] = result

                    self.emit_event(
                        KernelEventType.TOOL_FAILED,
                        task_id=task_id,
                        tool_name=tool_name,
                        error=result.error,
                    )

                    print(
                        f"'{tool_name}' failed "
                        f"on attempt {attempt}: "
                        f"{result.error}"
                    )

                    return result

                # --------------------------------------------------
                # RETRYABLE FAILURE
                # --------------------------------------------------

                print(
                    f"'{tool_name}' failed "
                    f"on attempt {attempt}; "
                    f"retrying..."
                )

                if attempt < self.max_retries:

                    await asyncio.sleep(
                        0.5 * attempt
                    )

            except Exception as exc:

                error_message = str(exc)

                print(
                    f"Exception while executing "
                    f"'{tool_name}': "
                    f"{error_message}"
                )

                last_result = ToolResult(
                    task_id=task_id,
                    tool_name=tool_name,
                    success=False,
                    error=error_message,
                    retryable=False,
                )

                task.results[
                    tool_name
                ] = last_result

                self.emit_event(
                    KernelEventType.TOOL_FAILED,
                    task_id=task_id,
                    tool_name=tool_name,
                    error=error_message,
                )

                return last_result

        # --------------------------------------------------
        # RETRIES EXHAUSTED
        # --------------------------------------------------

        if last_result is not None:

            task.results[
                tool_name
            ] = last_result

            self.emit_event(
                KernelEventType.TOOL_FAILED,
                task_id=task_id,
                tool_name=tool_name,
                error=last_result.error,
            )

            return last_result

        result = ToolResult(
            task_id=task_id,
            tool_name=tool_name,
            success=False,
            error=(
                f"Tool '{tool_name}' failed "
                f"without returning a result."
            ),
            retryable=False,
        )

        task.results[
            tool_name
        ] = result

        return result

    # ======================================================
    # EXECUTE MULTIPLE TOOLS
    # ======================================================

    async def execute_multiple_tools(
        self,
        task_id: str,
        tool_calls: list[dict[str, Any]],
    ) -> list[ToolResult]:

        results: list[ToolResult] = []

        for tool_call in tool_calls:

            tool_name = tool_call[
                "tool_name"
            ]

            arguments = tool_call.get(
                "arguments",
                {}
            )

            result = await self.execute_tool(
                tool_name,
                task_id,
                **arguments,
            )

            results.append(result)

        return results

    # ======================================================
    # CHECKPOINT
    # ======================================================

    def checkpoint(
        self,
        task_id: str,
        checkpoint: str,
    ) -> None:

        if self.current_task is None:
            raise RuntimeError(
                "No active Kernel task."
            )

        if self.current_task_id != task_id:
            raise RuntimeError(
                "Task mismatch."
            )

        self.current_task.checkpoint = checkpoint

        self.emit_event(
            KernelEventType.CHECKPOINT_CREATED,
            task_id=task_id,
            checkpoint=checkpoint,
        )

        print(
            f"Checkpoint created: "
            f"{checkpoint}"
        )

    # ======================================================
    # COMPLETE TASK
    # ======================================================

    def complete_task(
        self,
        task_id: str,
    ) -> Task:

        if self.current_task is None:
            raise RuntimeError(
                "No active Kernel task."
            )

        if self.current_task_id != task_id:
            raise RuntimeError(
                "Task mismatch."
            )

        self.current_task.status = TaskStatus.DONE

        self.emit_event(
            KernelEventType.TASK_COMPLETED,
            task_id=task_id,
        )

        print(
            f"Task completed: {task_id}"
        )

        return self.current_task

    # ======================================================
    # FAIL TASK
    # ======================================================

    def fail_task(
        self,
        task_id: str,
        error: str,
    ) -> Task:

        if self.current_task is None:
            raise RuntimeError(
                "No active Kernel task."
            )

        if self.current_task_id != task_id:
            raise RuntimeError(
                "Task mismatch."
            )

        self.current_task.status = TaskStatus.FAILED

        self.emit_event(
            KernelEventType.TASK_FAILED,
            task_id=task_id,
            error=error,
        )

        print(
            f"Task failed: "
            f"{task_id} | {error}"
        )

        return self.current_task

    # ======================================================
    # CANCEL TASK
    # ======================================================

    def cancel_task(
        self,
        task_id: str,
    ) -> Task:

        if self.current_task is None:
            raise RuntimeError(
                "No active Kernel task."
            )

        if self.current_task_id != task_id:
            raise RuntimeError(
                "Task mismatch."
            )

        self.current_task.status = TaskStatus.CANCELLED

        self.emit_event(
            KernelEventType.TASK_CANCELLED,
            task_id=task_id,
        )

        print(
            f"Task cancelled: {task_id}"
        )

        return self.current_task

    # ======================================================
    # CORRECTION
    # ======================================================

    def correct_task(
        self,
        task_id: str,
        correction: str,
    ) -> Task:

        if self.current_task is None:
            raise RuntimeError(
                "No active Kernel task."
            )

        if self.current_task_id != task_id:
            raise RuntimeError(
                "Task mismatch."
            )

        self.current_task.goal = correction

        self.current_task.status = TaskStatus.RUNNING

        self.emit_event(
            KernelEventType.TASK_CORRECTED,
            task_id=task_id,
            data={
                "correction": correction
            },
        )

        print(
            f"Task corrected: "
            f"{task_id}"
        )

        return self.current_task

    # ======================================================
    # GET CURRENT TASK
    # ======================================================

    def get_current_task(
        self,
    ) -> Task | None:

        return self.current_task

    # ======================================================
    # GET TASK
    # ======================================================

    def get_task(
        self,
        task_id: str,
    ) -> Task | None:

        if (
            self.current_task is not None
            and self.current_task.task_id == task_id
        ):
            return self.current_task

        return None

    # ======================================================
    # GET TOOL
    # ======================================================

    def get_tool(
        self,
        tool_name: str,
    ) -> BaseTool | None:

        return self.tools.get(
            tool_name
        )

    # ======================================================
    # GET TOOLS
    # ======================================================

    def get_tools(
        self,
    ) -> dict[str, BaseTool]:

        return self.tools

    # ======================================================
    # MULTI-STEP WORKFLOW
    # ======================================================

    async def run_workflow(
        self,
        goal: str,
        steps: list[dict[str, Any]],
    ) -> Task:

        task = self.start_task(
            goal
        )

        try:

            for index, step in enumerate(
                steps,
                start=1,
            ):

                task.current_step = index

                tool_name = step[
                    "tool_name"
                ]

                arguments = step.get(
                    "arguments",
                    {},
                )

                step_name = step.get(
                    "step_name",
                    f"Step {index}",
                )

                print(
                    f"\nSTEP {index}: "
                    f"{step_name}"
                )

                self.emit_event(
                    KernelEventType.STEP_STARTED,
                    task_id=task.task_id,
                    tool_name=tool_name,
                    step_name=step_name,
                )

                result = await self.execute_tool(
                    tool_name,
                    task.task_id,
                    **arguments,
                )

                if not result.success:

                    self.fail_task(
                        task.task_id,
                        result.error
                        or "Tool execution failed.",
                    )

                    return task

                self.emit_event(
                    KernelEventType.STEP_COMPLETED,
                    task_id=task.task_id,
                    tool_name=tool_name,
                    step_name=step_name,
                    data=result.data,
                )

            self.complete_task(
                task.task_id
            )

            return task

        except Exception as exc:

            self.fail_task(
                task.task_id,
                str(exc),
            )

            return task


# ==========================================================
# DIRECT EXECUTION
# ==========================================================

if __name__ == "__main__":

    async def main():

        kernel = Kernel()

        # --------------------------------------------------
        # Show all registered tools
        # --------------------------------------------------

        print("\nRegistered tools:")

        for tool_name in kernel.get_tools():
            print(f"  - {tool_name}")

        # --------------------------------------------------
        # Basic smart-home test
        # --------------------------------------------------

        task = kernel.start_task(
            "Test Samsung AI Kernel"
        )

        result = await kernel.execute_tool(
            "smart_home",
            task.task_id,
            device="living_room_light",
            action="turn_on",
        )

        print(
            "\nTool result:"
        )

        print(
            result
        )

        kernel.complete_task(
            task.task_id
        )


    asyncio.run(main())