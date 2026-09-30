from typing import Any

from tool_base import BaseTool
from tool_interface import ToolResult


class EmployeePlannerTool(BaseTool):

    def __init__(self):
        self.employees = {}

    @property
    def name(self) -> str:
        return "employee_planner"

    async def run(
        self,
        task_id: str,
        **kwargs: Any
    ) -> ToolResult:

        action = kwargs.get("action")
        employee = kwargs.get("employee")
        date = kwargs.get("date")
        task = kwargs.get("task")
        status = kwargs.get("status")

        try:
            if action == "add_task":
                return self._add_task(
                    task_id,
                    employee,
                    date,
                    task
                )

            if action == "remove_task":
                return self._remove_task(
                    task_id,
                    employee,
                    date,
                    task
                )

            if action == "get_schedule":
                return self._get_schedule(
                    task_id,
                    employee,
                    date
                )

            if action == "update_status":
                return self._update_status(
                    task_id,
                    employee,
                    date,
                    task,
                    status
                )

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error=f"Unknown action: {action}",
                retryable=False,
            )

        except Exception as exc:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error=str(exc),
                retryable=False,
            )

    def _add_task(
        self,
        task_id: str,
        employee: str,
        date: str,
        task: str
    ) -> ToolResult:

        if not employee or not date or not task:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Employee, date and task are required.",
                retryable=False,
            )

        employee = employee.strip().lower()

        if employee not in self.employees:
            self.employees[employee] = {}

        if date not in self.employees[employee]:
            self.employees[employee][date] = []

        self.employees[employee][date].append({
            "task": task,
            "status": "pending"
        })

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "employee": employee,
                "date": date,
                "task": task,
                "status": "pending",
                "message": (
                    f"Task added for {employee} on {date}."
                )
            },
        )

    def _remove_task(
        self,
        task_id: str,
        employee: str,
        date: str,
        task: str
    ) -> ToolResult:

        if not employee or not date or not task:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Employee, date and task are required.",
                retryable=False,
            )

        employee = employee.strip().lower()

        if employee not in self.employees:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Employee not found.",
                retryable=False,
            )

        if date not in self.employees[employee]:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="No schedule found for that date.",
                retryable=False,
            )

        tasks = self.employees[employee][date]

        for item in tasks:
            if item["task"].lower() == task.lower():
                tasks.remove(item)

                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=True,
                    data={
                        "employee": employee,
                        "date": date,
                        "task": task,
                        "message": "Task removed successfully."
                    },
                )

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=False,
            error="Task not found.",
            retryable=False,
        )

    def _get_schedule(
        self,
        task_id: str,
        employee: str | None,
        date: str | None
    ) -> ToolResult:

        if employee:
            employee = employee.strip().lower()

            if employee not in self.employees:
                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=True,
                    data={
                        "employee": employee,
                        "schedule": {}
                    },
                )

            if date:
                schedule = {
                    date: self.employees[employee].get(
                        date,
                        []
                    )
                }
            else:
                schedule = self.employees[employee]

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data={
                    "employee": employee,
                    "schedule": schedule
                },
            )

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "employees": self.employees
            },
        )

    def _update_status(
        self,
        task_id: str,
        employee: str,
        date: str,
        task: str,
        status: str
    ) -> ToolResult:

        if not employee or not date or not task or not status:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error=(
                    "Employee, date, task and status "
                    "are required."
                ),
                retryable=False,
            )

        employee = employee.strip().lower()

        if employee not in self.employees:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Employee not found.",
                retryable=False,
            )

        if date not in self.employees[employee]:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="No schedule found for that date.",
                retryable=False,
            )

        for item in self.employees[employee][date]:

            if item["task"].lower() == task.lower():

                item["status"] = status

                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=True,
                    data={
                        "employee": employee,
                        "date": date,
                        "task": task,
                        "status": status,
                        "message": (
                            "Task status updated successfully."
                        )
                    },
                )

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=False,
            error="Task not found.",
            retryable=False,
        )


if __name__ == "__main__":
    import asyncio

    async def main():

        tool = EmployeePlannerTool()

        task_id = "demo-task"

        # Add task
        result = await tool.run(
            task_id,
            action="add_task",
            employee="John",
            date="2026-09-29",
            task="Team meeting"
        )
        print(result)

        # Get schedule
        result = await tool.run(
            task_id,
            action="get_schedule",
            employee="John",
            date="2026-09-29"
        )
        print(result)

        # Update status
        result = await tool.run(
            task_id,
            action="update_status",
            employee="John",
            date="2026-09-29",
            task="Team meeting",
            status="completed"
        )
        print(result)

        # Get updated schedule
        result = await tool.run(
            task_id,
            action="get_schedule",
            employee="John"
        )
        print(result)

        # Remove task
        result = await tool.run(
            task_id,
            action="remove_task",
            employee="John",
            date="2026-09-29",
            task="Team meeting"
        )
        print(result)

    asyncio.run(main())