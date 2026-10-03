import os

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
)

from livekit.plugins import google

from kernel import Kernel
from livekit_kernel_tools import LiveKitKernelTools


# ============================================================
# LIVEKIT SERVER
# ============================================================

server = AgentServer()


# ============================================================
# SAMSUNG AI KERNEL AGENT
# ============================================================

class SamsungAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
You are Samsung AI Kernel, a helpful general-purpose AI voice assistant.

GENERAL CONVERSATION
- Talk naturally with the user.
- Answer general questions normally.
- Help with explanations, learning, brainstorming, interview preparation,
  coding discussions, career questions, and casual conversation.
- Do not unnecessarily use tools for normal conversation.
- Keep spoken responses clear and reasonably concise.

AVAILABLE SAMSUNG AI KERNEL TOOLS

1. smart_home
Use this when the user wants to control a smart-home device.

2. flight_search
Use this when the user wants to search for flights.
Ask for missing origin or destination.

3. hotel_search
Use this when the user wants to search for hotels.
Ask for missing required information.

4. doctor_appointment
Use this when the user wants to manage a doctor appointment.
Ask for missing required information.

5. kitchen_assistant
Use this for kitchen inventory and recipe management.

Possible actions:
- add ingredient
- remove ingredient
- check inventory
- add recipe
- get recipe
- clear inventory

6. study_helper
Use this for study-topic management.

Possible actions:
- add topic
- remove topic
- get topics
- mark completed
- clear subject

7. employee_planner
Use this for employee task and schedule management.

Possible actions:
- add task
- remove task
- get schedule
- update status

TOOL RULES

- Use the appropriate tool when the user's request requires an executable action.
- Do not claim a tool is unavailable when it is available.
- Ask for missing required information instead of inventing it.
- Use information provided in follow-up messages.
- Do not call tools unnecessarily.
- After successful tool execution, clearly tell the user what happened.
- If a tool fails, explain the error naturally.
- Never claim an action succeeded if the tool failed.

You are a general-purpose assistant, not a tool-only assistant.
Interview preparation, explanations, career questions, technical questions,
and normal conversation should be handled directly unless a tool is needed.
"""
        )


# ============================================================
# RTC SESSION
# ============================================================

@server.rtc_session()
async def entrypoint(ctx: JobContext):

    print("[LIVEKIT] Starting Samsung AI Kernel...")

    # --------------------------------------------------------
    # Kernel
    # --------------------------------------------------------

    kernel = Kernel()

    # --------------------------------------------------------
    # Kernel -> LiveKit tool bridge
    # --------------------------------------------------------

    kernel_tools = LiveKitKernelTools(kernel)

    tools = kernel_tools.get_tools()

    print("[LIVEKIT] Available tools:")

    for tool in tools:
        print(f"  - {getattr(tool, 'name', str(tool))}")

    # --------------------------------------------------------
    # Gemini API key
    # --------------------------------------------------------

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set."
        )

    # --------------------------------------------------------
    # Gemini Live
    # --------------------------------------------------------

    realtime_model = google.realtime.RealtimeModel(
        model="gemini-3.8-live",
        api_key=api_key,
        voice="Puck",
        temperature=0.7,
    )

    # --------------------------------------------------------
    # Agent Session
    # --------------------------------------------------------

    session = AgentSession(
        llm=realtime_model,
        tools=tools,
    )

    # --------------------------------------------------------
    # Start
    # --------------------------------------------------------

    await session.start(
        room=ctx.room,
        agent=SamsungAgent(),
    )

    print("[LIVEKIT] AgentSession started")
    print("[LIVEKIT] Gemini model: gemini-3.8-live")
    print("[LIVEKIT] Gemini Live is ready for microphone input.")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    cli.run_app(server)