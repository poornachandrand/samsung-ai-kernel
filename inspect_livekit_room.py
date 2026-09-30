import asyncio
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def main():
    lk = api.LiveKitAPI(
        url=os.environ["LIVEKIT_URL"],
        api_key=os.environ["LIVEKIT_API_KEY"],
        api_secret=os.environ["LIVEKIT_API_SECRET"],
    )

    rooms = await lk.room.list_rooms(api.ListRoomsRequest())

    print("LIVEKIT ROOMS")
    for room in rooms.rooms:
        print("Room:", room.name)
        print("SID:", room.sid)
        print("Participants:", room.num_participants)

    await lk.aclose()

if __name__ == "__main__":
    asyncio.run(main())
