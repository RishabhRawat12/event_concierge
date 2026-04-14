import json
import logging
from google import genai
from google.genai import types
from schemas.models import ItineraryResponse, UserConstraints, Event
from utils.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """
    A service class responsible for managing connections and prompt matrices injected into the Gemini 1.5 Flash endpoint natively handling structured Pydantic payload generations.
    """
    def __init__(self) -> None:
        """
        Initializes the service by securely parsing and caching API keys and loading local mock structural event definitions from standard storage.
        """
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        with open("mock_events.json", "r") as f:
            self.mock_events = json.load(f)

    async def generate_itinerary(self, constraints: UserConstraints, distance_matrix_info: str, current_weather: str = "Unknown") -> ItineraryResponse:
        """
        Calls the Gemini engine natively enforcing strict asynchronous schemas driven by distance paths and weather.

        Args:
            constraints (UserConstraints): The spatial and timeline definitions generated contextually.
            distance_matrix_info (str): The precalculated text string layout denoting coordinate transition delays.
            current_weather (str): Current localized weather string parsed from upstream monitors.

        Returns:
            ItineraryResponse: A strictly mapped layout of sequence-based events bound to physical parameters.
        """        
        prompt = f"""
        You are an expert Context-Aware Event Concierge. Your task is to generate a time-optimized, conflict-free itinerary.
        The user has provided the following constraints:
        - User Start Location: Lat: {constraints.user_location.latitude}, Lng: {constraints.user_location.longitude}
        - Time Window: {constraints.start_time} to {constraints.end_time}
        - Preferred Topics: {', '.join(constraints.preferred_topics)}
        
        Weather Context:
        The current weather is '{current_weather}'.
        If the weather is 'Rain', 'Snow', or 'Storm', prioritize indoor events from the mock list and increase the transition_time_seconds for walking by 50%.
        If the weather is 'Clear', prioritize outdoor networking sessions.

        Here are the available mocked events:
        {json.dumps(self.mock_events, indent=2)}

        Here is the relevant distance matrix showing walking times in seconds between these locations:
        {distance_matrix_info}
        
        Using ONLY the provided events, select the most relevant events based on the user's topics.
        Ensure that the event times do not overlap and that the user has enough transition time (based on the distance matrix) to walk from one event to the next.
        Make sure you calculate time properly.
        Return the itinerary as strict JSON conforming exactly to the requested schema. Do not output any markdown formatting, only raw JSON.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ItineraryResponse,
                    temperature=0.0
                )
            )
            return ItineraryResponse.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Gemini API failure: {e}")
            return ItineraryResponse(
                itinerary=[
                    Event(
                        event_name="AI & Future of Work Keynote (Fallback)",
                        start_time="09:00 AM",
                        end_time="10:00 AM",
                        walking_directions="Proceed to the main hall. (Generated via offline fallback due to high API demand).",
                        transition_time_seconds=300
                    ),
                    Event(
                        event_name="Networking Lunch (Fallback)",
                        start_time="12:00 PM",
                        end_time="01:00 PM",
                        walking_directions="Walk to the cafeteria.",
                        transition_time_seconds=300
                    )
                ]
            )

gemini_service = GeminiService()
