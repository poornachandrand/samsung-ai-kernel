import asyncio
import os

from dotenv import load_dotenv
from livekit import api


async def main():
    print("=" * 70)
    print("LIVEKIT ROOM & PARTICIPANT TEST")
    print("=" * 70)

    load_dotenv()

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    assert url, "LIVEKIT_URL is missing"
    assert api_key, "LIVEKIT_API_KEY is missing"
    assert api_secret, "LIVEKIT_API_SECRET is missing"

    print("LiveKit credentials loaded           ✓")

    room_name = "samsung-ai-kernel-test"
    participant_identity = "person3-kernel-test"

    livekit_api = api.LiveKitAPI(
        url=url,
        api_key=api_key,
        api_secret=api_secret,
    )

    try:
        # Create the test room.
        await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
            )
        )

        print("LiveKit room creation request sent  ✓")
        print(f"Room: {room_name}")

        # Create participant access token.
        token = (
            api.AccessToken(api_key, api_secret)
            .with_identity(participant_identity)
            .with_name("Person 3 Kernel Test")
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                )
            )
            .to_jwt()
        )

        assert token
        print("Participant access token created   ✓")
        print(f"Participant: {participant_identity}")

        print()
        print("LiveKit room + participant setup successful.")
        print("Skipping immediate room-list verification.")

    finally:
        await livekit_api.aclose()

    print()
    print("=" * 70)
    print("LIVEKIT ROOM & PARTICIPANT TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())