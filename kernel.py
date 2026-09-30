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
            status=TaskStatus.RUNNING
        )

        self.current_task = task

        self.current_task_id = (
            task.task_id
        )

        self.emit_event(
            KernelEventType.TASK_STARTED,
            task.task_id,
            data={
                "goal": goal
            }
        )

        print(
            f"Started task: {task.task_id}"
        )

        print(
            f"Goal: {goal}"
        )

        return task

    # ======================================================
    # EXECUTE ONE TOOL
    # ======================================================

    async def execute_tool(
        self,
        tool_name: str,
        task_id: str,
        **kwargs: Any
    ) -> ToolResult:

        # --------------------------------------------------
        # TASK VALIDATION
        # --------------------------------------------------

        if self.current_task is None:

            raise RuntimeError(
                "No active task."
            )

        if task_id != self.current_task.task_id:

            raise RuntimeError(
                "Task ID does not match "
                "the active task."
            )

        if self.current_task.status in (
            TaskStatus.CANCELLED,
            TaskStatus.DONE,
            TaskStatus.FAILED
        ):

            raise RuntimeError(
                "Task is no longer active."
            )

        # --------------------------------------------------
        # TOOL VALIDATION
        # --------------------------------------------------

        if tool_name not in self.tools:

            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        tool = self.tools[
            tool_name
        ]

        max_attempts = self.max_retries

        # --------------------------------------------------
        # RETRY LOOP
        # --------------------------------------------------

        for attempt in range(
            1,
            max_attempts + 1
        ):

            # --------------------------------------------------
            # CHECK CANCELLATION
            # --------------------------------------------------

            if (
                self.current_task.status
                == TaskStatus.CANCELLED
            ):

                raise asyncio.CancelledError

            # --------------------------------------------------
            # TOOL START EVENT
            # --------------------------------------------------

            self.emit_event(
                KernelEventType.TOOL_STARTED,
                task_id,
                tool_name=tool_name,
                data={
                    "attempt": attempt
                }
            )

            print(
                f"Executing '{tool_name}' "
                f"(attempt {attempt}/"
                f"{max_attempts})"
            )

            # --------------------------------------------------
            # RUN TOOL
            # --------------------------------------------------

            try:

                result = await tool.run(
                    task_id=task_id,
                    **kwargs
                )

            except asyncio.CancelledError:

                print(
                    f"Execution of "
                    f"'{tool_name}' "
                    f"was cancelled."
                )

                raise

            except Exception as error:

                self.emit_event(
                    KernelEventType.TOOL_FAILED,
                    task_id,
                    tool_name=tool_name,
                    data={
                        "attempt": attempt
                    },
                    error=str(error)
                )

                print(
                    f"'{tool_name}' "
                    f"raised an exception: "
                    f"{error}"
                )

                if attempt >= max_attempts:

                    self.current_task.status = (
                        TaskStatus.FAILED
                    )

                    self.emit_event(
                        KernelEventType.TASK_FAILED,
                        task_id,
                        tool_name=tool_name,
                        error=str(error)
                    )

                    raise

                self.current_task.retry_count += 1

                await asyncio.sleep(
                    0.2
                )

                continue

            # --------------------------------------------------
            # LATE / STALE RESULT PROTECTION
            # --------------------------------------------------

            if self.current_task is None:

                raise asyncio.CancelledError

            if (
                self.current_task.task_id
                != task_id
            ):

                raise RuntimeError(
                    "Task ID does not match "
                    "the active task."
                )

            if (
                self.current_task.status
                == TaskStatus.CANCELLED
            ):

                raise asyncio.CancelledError

            # --------------------------------------------------
            # SUCCESS
            # --------------------------------------------------

            if result.success:

                self.current_task.results[
                    tool_name
                ] = result

                self.emit_event(
                    KernelEventType.TOOL_COMPLETED,
                    task_id,
                    tool_name=tool_name,
                    data={
                        "attempt": attempt,
                        "result": result.data
                    }
                )

                print(
                    f"'{tool_name}' "
                    f"succeeded on attempt "
                    f"{attempt}."
                )

                return result

            # --------------------------------------------------
            # TOOL FAILURE
            # --------------------------------------------------

            self.emit_event(
                KernelEventType.TOOL_FAILED,
                task_id,
                tool_name=tool_name,
                data={
                    "attempt": attempt
                },
                error=result.error
            )

            # --------------------------------------------------
            # RETRYABLE FAILURE
            # --------------------------------------------------

            if (
                result.retryable
                and attempt < max_attempts
            ):

                self.current_task.retry_count += 1

                print(
                    f"'{tool_name}' "
                    f"failed but is retryable."
                )

                await asyncio.sleep(
                    0.2
                )

                continue

            # --------------------------------------------------
            # FINAL FAILURE
            # --------------------------------------------------

            self.current_task.results[
                tool_name
            ] = result

            print(
                f"'{tool_name}' "
                f"failed permanently."
            )

            return result

        raise RuntimeError(
            "Unexpected tool execution state."
        )

    # ======================================================
    # MULTIPLE TOOLS
    # ======================================================

    async def execute_multiple_tools(
        self,
        task_id: str,
        tool_requests: list[
            dict[str, Any]
        ]
    ) -> dict[
        str,
        ToolResult
    ]:

        print(
            f"Executing "
            f"{len(tool_requests)} "
            f"tools..."
        )

        tasks = []

        for request in tool_requests:

            tool_name = request[
                "tool_name"
            ]

            # Support both APIs.
            kwargs = request.get(
                "arguments"
            )

            if kwargs is None:

                kwargs = request.get(
                    "kwargs",
                    {}
                )

            tasks.append(
                self.execute_tool(
                    tool_name,
                    task_id,
                    **kwargs
                )
            )

        results_list = await asyncio.gather(
            *tasks
        )

        results = {}

        for result in results_list:

            results[
                result.tool_name
            ] = result

        return results

    # ======================================================
    # CHECKPOINT
    # ======================================================

    def save_checkpoint(
        self,
        checkpoint: str,
        step_name: str,
        **data: Any
    ) -> None:

        if self.current_task is None:

            raise RuntimeError(
                "No active task."
            )

        self.current_task.current_step += 1

        self.current_task.checkpoint = (
            checkpoint
        )

        self.current_task.slots.update(
            data
        )

        self.current_task.completed_steps.append(
            step_name
        )

        self.emit_event(
            KernelEventType.CHECKPOINT_SAVED,
            self.current_task.task_id,
            step_name=step_name,
            checkpoint=checkpoint,
            data=data
        )

        print()

        print(
            "Checkpoint saved:"
        )

        print(
            f"Step: "
            f"{self.current_task.current_step}"
        )

        print(
            f"Name: "
            f"{step_name}"
        )

        print(
            f"Checkpoint: "
            f"{checkpoint}"
        )

        if data:

            print(
                f"Stored data: {data}"
            )

    # ======================================================
    # COMPLETE TASK
    # ======================================================

    def complete_current_task(
        self
    ) -> None:

        if self.current_task is None:

            return

        if (
            self.current_task.status
            == TaskStatus.CANCELLED
        ):

            return

        self.current_task.status = (
            TaskStatus.DONE
        )

        self.current_task.checkpoint = (
            "task_completed"
        )

        self.emit_event(
            KernelEventType.TASK_COMPLETED,
            self.current_task.task_id
        )

        print(
            f"Task completed: "
            f"{self.current_task.task_id}"
        )

    # ======================================================
    # FAIL TASK
    # ======================================================

    def fail_current_task(
        self
    ) -> None:

        if self.current_task is None:

            return

        if (
            self.current_task.status
            == TaskStatus.CANCELLED
        ):

            return

        self.current_task.status = (
            TaskStatus.FAILED
        )

        self.emit_event(
            KernelEventType.TASK_FAILED,
            self.current_task.task_id
        )

        print(
            f"Task failed: "
            f"{self.current_task.task_id}"
        )

    # ======================================================
    # CANCEL TASK
    # ======================================================

    def cancel_current_task(
        self
    ) -> None:

        if self.current_task is None:

            return

        if self.current_task.status in (
            TaskStatus.DONE,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED
        ):

            return

        task_id = self.current_task.task_id

        self.current_task.status = (
            TaskStatus.CANCELLED
        )

        self.current_task.checkpoint = (
            "task_cancelled"
        )

        self.emit_event(
            KernelEventType.TASK_CANCELLED,
            task_id
        )

        print(
            f"Task cancelled: "
            f"{task_id}"
        )

        if (
            self._current_async_task
            and not self._current_async_task.done()
        ):

            self._current_async_task.cancel()

    # ======================================================
    # USER CORRECTION / INTERRUPTION
    # ======================================================

    def handle_user_correction(
        self,
        new_goal: str
    ) -> Task:

        old_task_id = None

        if self.current_task:

            old_task_id = (
                self.current_task.task_id
            )

            self.cancel_current_task()

        print()

        print(
            "Starting corrected task..."
        )

        new_task = self.start_task(
            goal=new_goal
        )

        print(
            f"Previous task: "
            f"{old_task_id}"
        )

        print(
            f"New task: "
            f"{new_task.task_id}"
        )

        return new_task

    # ======================================================
    # TASK GETTERS
    # ======================================================

    def get_current_task(
        self
    ) -> Task | None:

        return self.current_task

    def get_task_status(
        self
    ) -> TaskStatus | None:

        if self.current_task is None:

            return None

        return self.current_task.status

    def get_registered_tools(
        self
    ) -> list[str]:

        return list(
            self.tools.keys()
        )

    # ======================================================
    # MULTI-STEP WORKFLOW TEST
    # ======================================================

    async def multi_step_workflow_test(
        self
    ) -> bool:

        print()

        print(
            "=" * 70
        )

        print(
            "          MULTI-STEP WORKFLOW TEST"
        )

        print(
            "=" * 70
        )

        task = self.start_task(
            goal=(
                "Plan a trip from "
                "Bengaluru to Delhi."
            )
        )

        print()

        print(
            "WORKFLOW:"
        )

        print(
            "Step 1 → Search flight"
        )

        print(
            "Step 2 → Search hotel"
        )

        print(
            "Step 3 → Finalize"
        )

        # --------------------------------------------------
        # STEP 1
        # --------------------------------------------------

        print()

        print(
            "STEP 1: Flight search"
        )

        flight_result = await self.execute_tool(
            tool_name="flight_search",
            task_id=task.task_id,
            origin="Bengaluru",
            destination="Delhi"
        )

        if not flight_result.success:

            self.fail_current_task()

            return False

        self.save_checkpoint(
            checkpoint="flight_search_completed",
            step_name="flight_search",
            flight=flight_result.data
        )

        # --------------------------------------------------
        # STEP 2
        # --------------------------------------------------

        print()

        print(
            "STEP 2: Hotel search"
        )

        hotel_result = await self.execute_tool(
            tool_name="hotel_search",
            task_id=task.task_id,
            city="Delhi"
        )

        if not hotel_result.success:

            self.fail_current_task()

            return False

        self.save_checkpoint(
            checkpoint="hotel_search_completed",
            step_name="hotel_search",
            hotel=hotel_result.data
        )

        # --------------------------------------------------
        # STEP 3
        # --------------------------------------------------

        print()

        print(
            "STEP 3: Finalizing workflow"
        )

        self.save_checkpoint(
            checkpoint="workflow_ready",
            step_name="finalization"
        )

        self.complete_current_task()

        # --------------------------------------------------
        # VERIFY
        # --------------------------------------------------

        print()

        print(
            "Final task status:"
        )

        print(
            task.status
        )

        print()

        print(
            "Current step:"
        )

        print(
            task.current_step
        )

        print()

        print(
            "Checkpoint:"
        )

        print(
            task.checkpoint
        )

        print()

        print(
            "Completed steps:"
        )

        print(
            task.completed_steps
        )

        print()

        print(
            "Stored workflow data:"
        )

        print(
            task.slots
        )

        if task.status != TaskStatus.DONE:

            return False

        if task.current_step != 3:

            return False

        if task.checkpoint != (
            "task_completed"
        ):

            return False

        if len(
            task.completed_steps
        ) != 3:

            return False

        if "flight" not in task.slots:

            return False

        if "hotel" not in task.slots:

            return False

        print()

        print(
            "MULTI-STEP WORKFLOW TEST PASSED"
        )

        return True


# ==========================================================
# MAIN
# ==========================================================

async def main():

    kernel = Kernel()

    passed = await (
        kernel.multi_step_workflow_test()
    )

    print()

    print(
        "=" * 70
    )

    if passed:

        print(
            "       KERNEL MULTI-STEP "
            "WORKFLOW PASSED"
        )

    else:

        print(
            "       KERNEL MULTI-STEP "
            "WORKFLOW FAILED"
        )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print()

        print(
            "Program interrupted by user."
        )