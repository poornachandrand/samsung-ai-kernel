import asyncio
import os

from dotenv import load_dotenv
from livekit import api


async def main():
    print("=" * 70)
    print("LIVEKIT CONNECTION TEST")
    print("=" * 70)

    load_dotenv()

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    assert url, "LIVEKIT_URL is missing"
    assert api_key, "LIVEKIT_API_KEY is missing"
    assert api_secret, "LIVEKIT_API_SECRET is missing"

    print("LiveKit URL loaded                 ✓")
    print("LiveKit API key loaded             ✓")
    print("LiveKit API secret loaded          ✓")

    # Create an API client using the team's LiveKit project.
    livekit_api = api.LiveKitAPI(
        url=url,
        api_key=api_key,
        api_secret=api_secret,
    )

    # Ask LiveKit for the list of rooms.
    rooms = await livekit_api.room.list_rooms(
        api.ListRoomsRequest()
    )

    print("LiveKit API connection successful  ✓")
    print(f"Accessible rooms: {len(rooms.rooms)}")

    await livekit_api.aclose()

    print()
    print("=" * 70)
    print("LIVEKIT CONNECTION TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())