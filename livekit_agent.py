import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobRequest,
    cli,
)

from gemini_kernel import GeminiKernelBridge
from livekit_gemini_adapter import GeminiLiveKitLLM
from livekit_kernel_tools import LiveKitKernelTools

load_dotenv()


class SamsungAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "You are the Samsung AI Kernel voice assistant. "
                "Help the user clearly and briefly. "
                "When the user asks for a flight, hotel, or smart-home "
                "action, use the appropriate available tool."
            )
        )


server = AgentServer()


async def accept_job(request: JobRequest):
    print(
        f"[LIVEKIT] Job request received: "
        f"{request.id} | room={request.room.name}"
    )

    await request.accept()

    print(f"[LIVEKIT] Job accepted: {request.id}")


@server.rtc_session(
    agent_name="samsung-ai-kernel",
    on_request=accept_job,
)
async def entrypoint(ctx: JobContext):
    print(f"[LIVEKIT] Entrypoint started: {ctx.room.name}")

    await ctx.connect()

    gemini_bridge = GeminiKernelBridge()

    kernel_tools = LiveKitKernelTools(
        gemini_bridge.kernel
    )

    livekit_llm = GeminiLiveKitLLM(
        gemini_bridge
    )

    tools = kernel_tools.get_tools()

    session = AgentSession(
        llm=livekit_llm,
        tools=tools,
    )

    await session.start(
        agent=SamsungAgent(),
        room=ctx.room,
    )

    print("[LIVEKIT] AgentSession started")
    print(
        "[LIVEKIT] Available tools:",
        [tool.id for tool in tools],
    )

    # Greeting deliberately has NO tools available.
    await session.generate_reply(
        instructions=(
            "Greet the user briefly and say exactly: "
            "Samsung AI Kernel is connected and ready."
        ),
        tools=[],
        tool_choice="none",
    )


if __name__ == "__main__":
    cli.run_app(server)