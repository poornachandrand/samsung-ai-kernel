import asyncio
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def main():
    room_name = "samsung-ai-kernel-test"
    agent_name = "samsung-ai-kernel"

    async with api.LiveKitAPI(
        url=os.environ["LIVEKIT_URL"],
        api_key=os.environ["LIVEKIT_API_KEY"],
        api_secret=os.environ["LIVEKIT_API_SECRET"],
    ) as lkapi:
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_name,
                room=room_name,
                metadata="{}"
            )
        )

        print("AGENT DISPATCH CREATED")
        print("Dispatch ID:", dispatch.id)
        print("Agent:", dispatch.agent_name)
        print("Room:", dispatch.room)

if __name__ == "__main__":
    asyncio.run(main())
