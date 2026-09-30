from typing import Any

from tool_base import BaseTool
from tool_interface import ToolResult


class StudyHelperTool(BaseTool):

    def __init__(self):
        self.study_plan = {}

    @property
    def name(self) -> str:
        return "study_helper"

    async def run(self, task_id: str, **kwargs: Any) -> ToolResult:

        action = kwargs.get("action")

        try:
            if action == "add_topic":
                return self._add_topic(
                    task_id,
                    kwargs.get("subject"),
                    kwargs.get("topic")
                )

            if action == "remove_topic":
                return self._remove_topic(
                    task_id,
                    kwargs.get("subject"),
                    kwargs.get("topic")
                )

            if action == "get_topics":
                return self._get_topics(
                    task_id,
                    kwargs.get("subject")
                )

            if action == "mark_completed":
                return self._mark_completed(
                    task_id,
                    kwargs.get("subject"),
                    kwargs.get("topic")
                )

            if action == "clear_subject":
                return self._clear_subject(
                    task_id,
                    kwargs.get("subject")
                )

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                data=None,
                error=f"Unknown action: {action}",
                retryable=False
            )

        except Exception as exc:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                data=None,
                error=str(exc),
                retryable=False
            )

    def _add_topic(
        self,
        task_id: str,
        subject: str,
        topic: str
    ) -> ToolResult:

        if not subject or not topic:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                data=None,
                error="Subject and topic are required.",
                retryable=False
            )

        subject = subject.lower()

        if subject not in self.study_plan:
            self.study_plan[subject] = []

        self.study_plan[subject].append({
            "topic": topic,
            "status": "pending"
        })

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "subject": subject,
                "topic": topic,
                "status": "pending",
                "message": f"{topic} added to {subject} study plan."
            },
            error=None,
            retryable=False
        )

    def _remove_topic(
        self,
        task_id: str,
        subject: str,
        topic: str
    ) -> ToolResult:

        subject = subject.lower() if subject else ""

        if subject not in self.study_plan:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                data=None,
                error=f"No study plan found for {subject}.",
                retryable=False
            )

        for item in self.study_plan[subject]:
            if item["topic"].lower() == topic.lower():
                self.study_plan[subject].remove(item)

                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=True,
                    data={
                        "subject": subject,
                        "topic": topic,
                        "message": "Topic removed successfully."
                    },
                    error=None,
                    retryable=False
                )

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=False,
            data=None,
            error=f"Topic '{topic}' not found.",
            retryable=False
        )

    def _get_topics(
        self,
        task_id: str,
        subject: str
    ) -> ToolResult:

        subject = subject.lower() if subject else ""

        topics = self.study_plan.get(subject, [])

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "subject": subject,
                "topics": topics
            },
            error=None,
            retryable=False
        )

    def _mark_completed(
        self,
        task_id: str,
        subject: str,
        topic: str
    ) -> ToolResult:

        subject = subject.lower() if subject else ""

        if subject not in self.study_plan:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                data=None,
                error=f"No study plan found for {subject}.",
                retryable=False
            )

        for item in self.study_plan[subject]:
            if item["topic"].lower() == topic.lower():
                item["status"] = "completed"

                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=True,
                    data={
                        "subject": subject,
                        "topic": topic,
                        "status": "completed",
                        "message": "Topic marked as completed."
                    },
                    error=None,
                    retryable=False
                )

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=False,
            data=None,
            error=f"Topic '{topic}' not found.",
            retryable=False
        )

    def _clear_subject(
        self,
        task_id: str,
        subject: str
    ) -> ToolResult:

        subject = subject.lower() if subject else ""

        self.study_plan.pop(subject, None)

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "subject": subject,
                "message": "Study plan cleared."
            },
            error=None,
            retryable=False
        )


if __name__ == "__main__":

    import asyncio

    async def demo():

        tool = StudyHelperTool()
        task_id = "study-demo"

        print(await tool.run(
            task_id,
            action="add_topic",
            subject="DSA",
            topic="Arrays"
        ))

        print(await tool.run(
            task_id,
            action="add_topic",
            subject="DSA",
            topic="Linked Lists"
        ))

        print(await tool.run(
            task_id,
            action="get_topics",
            subject="DSA"
        ))

        print(await tool.run(
            task_id,
            action="mark_completed",
            subject="DSA",
            topic="Arrays"
        ))

        print(await tool.run(
            task_id,
            action="get_topics",
            subject="DSA"
        ))

    asyncio.run(demo())