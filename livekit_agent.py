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
from livekit.plugins import google

from gemini_kernel import GeminiKernelBridge
from livekit_kernel_tools import LiveKitKernelTools


load_dotenv()


class SamsungAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "You are the Samsung AI Kernel voice assistant. "
                "Help the user clearly and briefly. "
                "When the user asks for a flight, hotel, or smart-home "
                "action, use the appropriate available tool. "
                "Always respond naturally and concisely."
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

    # Existing Samsung AI Kernel.
    # We are not changing the Kernel itself.
    gemini_bridge = GeminiKernelBridge()

    kernel_tools = LiveKitKernelTools(
        gemini_bridge.kernel
    )

    tools = kernel_tools.get_tools()

    # Real Gemini Live / Realtime API.
    realtime_model = google.realtime.RealtimeModel(
        model="gemini-3.8-live",
        api_key=os.environ["GOOGLE_API_KEY"],
        voice="Puck",
        temperature=0.7,
    )

    session = AgentSession(
        llm=realtime_model,
        tools=tools,
    )

    await session.start(
        agent=SamsungAgent(),
        room=ctx.room,
    )

    print("[LIVEKIT] AgentSession started")
    print("[LIVEKIT] Gemini model: gemini-3.8-live")
    print(
        "[LIVEKIT] Available tools:",
        [tool.id for tool in tools],
    )

    # Do not force an initial generate_reply().
    # Gemini Live will respond to actual user microphone input.
    print("[LIVEKIT] Gemini Live is ready for microphone input.")


if __name__ == "__main__":
    cli.run_app(server)