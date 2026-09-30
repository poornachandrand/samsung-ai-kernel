from typing import Any

from tool_base import BaseTool
from tool_interface import ToolResult


class SmartHomeTool(BaseTool):

    def __init__(self):
        self.devices = {
            "bedroom_light": {
                "type": "light",
                "state": "off",
            },
            "living_room_light": {
                "type": "light",
                "state": "off",
            },
            "bedroom_fan": {
                "type": "fan",
                "state": "off",
            },
            "living_room_fan": {
                "type": "fan",
                "state": "off",
            },
            "ac": {
                "type": "ac",
                "state": "off",
                "temperature": 24,
            },
        }

    @property
    def name(self) -> str:
        return "smart_home"

    async def run(
        self,
        task_id: str,
        **kwargs: Any
    ) -> ToolResult:

        action = kwargs.get("action")
        device = kwargs.get("device")
        temperature = kwargs.get("temperature")

        try:
            if action == "turn_on":
                return self._turn_on(task_id, device)

            if action == "turn_off":
                return self._turn_off(task_id, device)

            if action == "set_temperature":
                return self._set_temperature(
                    task_id,
                    temperature
                )

            if action == "get_status":
                return self._get_status(task_id, device)

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

    def _turn_on(
        self,
        task_id: str,
        device: str
    ) -> ToolResult:

        device = self._normalize_device(device)

        if device not in self.devices:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error=f"Unknown device: {device}",
                retryable=False,
            )

        self.devices[device]["state"] = "on"

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "device": device,
                "action": "turn_on",
                "message": f"{device} turned on.",
            },
        )

    def _turn_off(
        self,
        task_id: str,
        device: str
    ) -> ToolResult:

        device = self._normalize_device(device)

        if device not in self.devices:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error=f"Unknown device: {device}",
                retryable=False,
            )

        self.devices[device]["state"] = "off"

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "device": device,
                "action": "turn_off",
                "message": f"{device} turned off.",
            },
        )

    def _set_temperature(
        self,
        task_id: str,
        temperature: Any
    ) -> ToolResult:

        if temperature is None:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Temperature is required.",
                retryable=False,
            )

        try:
            temperature = int(temperature)
        except (TypeError, ValueError):
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Temperature must be a number.",
                retryable=False,
            )

        if not 16 <= temperature <= 30:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Temperature must be between 16°C and 30°C.",
                retryable=False,
            )

        self.devices["ac"]["state"] = "on"
        self.devices["ac"]["temperature"] = temperature

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "device": "ac",
                "action": "set_temperature",
                "temperature": temperature,
                "message": f"AC temperature set to {temperature}°C.",
            },
        )

    def _get_status(
        self,
        task_id: str,
        device: str | None
    ) -> ToolResult:

        if device:
            device = self._normalize_device(device)

            if device not in self.devices:
                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=False,
                    error=f"Unknown device: {device}",
                    retryable=False,
                )

            status = {
                "device": device,
                **self.devices[device],
            }

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data=status,
            )

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                name: details.copy()
                for name, details in self.devices.items()
            },
        )

    def _normalize_device(self, device: str) -> str:

        if not device:
            return ""

        device = device.lower().strip()

        aliases = {
            "bedroom light": "bedroom_light",
            "living room light": "living_room_light",
            "bedroom fan": "bedroom_fan",
            "living room fan": "living_room_fan",
            "air conditioner": "ac",
            "air conditioning": "ac",
            "a/c": "ac",
        }

        return aliases.get(device, device)


# Simple test when running this file directly
if __name__ == "__main__":
    import asyncio

    async def main():

        tool = SmartHomeTool()

        task_id = "demo-task"

        result = await tool.run(
            task_id,
            action="turn_on",
            device="bedroom light",
        )

        print(result)

        result = await tool.run(
            task_id,
            action="set_temperature",
            temperature=22,
        )

        print(result)

        result = await tool.run(
            task_id,
            action="get_status",
            device="bedroom light",
        )

        print(result)

    asyncio.run(main())