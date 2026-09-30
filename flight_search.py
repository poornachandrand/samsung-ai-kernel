import asyncio

from tool_base import BaseTool
from tool_interface import ToolResult


class FlightSearchTool(BaseTool):

    def __init__(self):
        self.attempt_count = 0

    @property
    def name(self) -> str:
        return "flight_search"

    async def run(
        self,
        task_id: str,
        **kwargs
    ) -> ToolResult:

        origin = kwargs.get("origin")
        destination = kwargs.get("destination")

        # -------------------------
        # Validate input
        # -------------------------

        if not origin:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Origin is required",
                retryable=False
            )

        if not destination:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Destination is required",
                retryable=False
            )

        # -------------------------
        # Count attempts
        # -------------------------

        self.attempt_count += 1

        print(f"\nFlight search attempt {self.attempt_count}")
        print(f"Searching: {origin} -> {destination}")

        await asyncio.sleep(1)

        # -------------------------
        # Simulate temporary failure
        # -------------------------

        if self.attempt_count == 1:
            print("Flight service temporarily failed.")

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Temporary flight service failure",
                retryable=True
            )

        # -------------------------
        # Success on second attempt
        # -------------------------

        print("Flight search completed.")

        result = {
            "origin": origin,
            "destination": destination,
            "message": f"Flight found from {origin} to {destination}"
        }

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data=result
        )