import json
import uuid
from typing import Any

import livekit.agents as agents
from livekit.agents import llm


class GeminiLiveKitLLM(llm.LLM):
    """
    Connects the existing GeminiKernelBridge to LiveKit's LLM interface.

    Gemini remains responsible for deciding which tool to call.
    LiveKit remains responsible for executing the registered tool.
    """

    def __init__(self, gemini_bridge):
        super().__init__()
        self._gemini_bridge = gemini_bridge

    @property
    def label(self) -> str:
        return "SamsungAIKernel.GeminiLiveKitLLM"

    @property
    def model(self) -> str:
        return "gemini"

    @property
    def provider(self) -> str:
        return "google"

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool] | None = None,
        conn_options: agents.APIConnectOptions = (
            agents.DEFAULT_API_CONNECT_OPTIONS
        ),
        **kwargs: Any,
    ) -> llm.LLMStream:
        return GeminiLiveKitStream(
            self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
            gemini_bridge=self._gemini_bridge,
        )


class GeminiLiveKitStream(llm.LLMStream):
    def __init__(
        self,
        llm_instance: GeminiLiveKitLLM,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool],
        conn_options: agents.APIConnectOptions,
        gemini_bridge,
    ):
        self._gemini_bridge = gemini_bridge

        super().__init__(
            llm_instance,
            chat_ctx=chat_ctx,
            tools=tools,
            conn_options=conn_options,
        )

    async def _run(self) -> None:
        try:
            prompt = self._build_prompt()

            response, _model_name = await self._generate(prompt)

            function_calls = getattr(
                response,
                "function_calls",
                None,
            ) or []

            if function_calls:
                for function_call in function_calls:
                    tool_call = llm.FunctionToolCall(
                        name=function_call.name,
                        arguments=json.dumps(
                            dict(function_call.args or {})
                        ),
                        call_id=(
                            getattr(function_call, "id", None)
                            or str(uuid.uuid4())
                        ),
                    )

                    chunk = llm.ChatChunk(
                        id=str(uuid.uuid4()),
                        delta=llm.ChoiceDelta(
                            role="assistant",
                            tool_calls=[tool_call],
                        ),
                    )

                    await self._event_ch.send(chunk)

                return

            text = self._extract_text(response)

            if text:
                chunk = llm.ChatChunk(
                    id=str(uuid.uuid4()),
                    delta=llm.ChoiceDelta(
                        role="assistant",
                        content=text,
                    ),
                )

                await self._event_ch.send(chunk)

        except Exception as exc:
            raise RuntimeError(
                f"GeminiLiveKitStream failed: {exc}"
            ) from exc

    def _build_prompt(self) -> str:
        messages: list[str] = []

        for item in self._chat_ctx.items:
            role = getattr(item, "role", None)
            content = getattr(item, "content", None)

            if content is None:
                continue

            if isinstance(content, list):
                content = " ".join(
                    str(part)
                    for part in content
                )

            messages.append(
                f"{role or 'user'}: {content}"
            )

        if not messages:
            return (
                "Respond briefly as the Samsung AI Kernel assistant."
            )

        return "\n".join(messages)

    async def _generate(self, prompt: str):
        generate_method = getattr(
            self._gemini_bridge,
            "generate",
            None,
        )

        if generate_method is None:
            raise RuntimeError(
                "Gemini bridge does not expose generate()."
            )

        result = await generate_method(
            contents=prompt,
            config=self._gemini_bridge.tool_config,
        )

        if isinstance(result, tuple) and len(result) == 2:
            return result

        return result, "unknown"

    @staticmethod
    def _extract_text(response: Any) -> str:
        if response is None:
            return ""

        text = getattr(
            response,
            "text",
            None,
        )

        if text:
            return str(text)

        if isinstance(response, str):
            return response

        return str(response)
