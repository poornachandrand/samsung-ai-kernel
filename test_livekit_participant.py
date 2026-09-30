import asyncio
import os
from dotenv import load_dotenv
from livekit import rtc, api

load_dotenv()

async def main():
    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]

    room_name = "samsung-ai-kernel-test"
    participant_identity = "person3-live-test"

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(participant_identity)
        .with_name("Person 3 Live Test")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
            )
        )
        .to_jwt()
    )

    room = rtc.Room()

    print("Connecting to LiveKit room...")
    await room.connect(url, token)

    print("CONNECTED TO ROOM")
    print("Room:", room.name)
    print("Participant:", room.local_participant.identity)
    print("Waiting 60 seconds for agent dispatch...")

    await asyncio.sleep(60)

    print("Disconnecting...")
    await room.disconnect()
    print("PARTICIPANT TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())
