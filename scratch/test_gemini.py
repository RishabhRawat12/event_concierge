import asyncio
from services.gemini import gemini_service
from schemas.models import UserConstraints, Coordinates
from dotenv import load_dotenv

async def test_itinerary():
    load_dotenv()
    print("Testing Itinerary Generation...")
    # Matches Coordinates and time pattern from models.py
    constraints = UserConstraints(
        user_location=Coordinates(latitude=37.7749, longitude=-122.4194),
        preferred_topics=["AI", "Art"],
        start_time="09:00 AM",
        end_time="05:00 PM"
    )
    try:
        await gemini_service.load_events()
        itinerary = await gemini_service.generate_itinerary(constraints, "", "Sunny")
        print("Success!")
        print(itinerary.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()

async def test_staff():
    load_dotenv()
    print("\nTesting Staff Protocol Generation...")
    try:
        protocol = await gemini_service.generate_staff_protocol("Main Entrance", "High Traffic")
        print("Success!")
        print(protocol.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_itinerary())
    asyncio.run(test_staff())
