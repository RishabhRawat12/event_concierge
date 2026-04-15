import json
import logging
import asyncio
from google import genai
from google.genai import types
from schemas.models import ItineraryResponse, UserConstraints, Event, StaffActionRequest, StaffActionResponse
from typing import Optional, Union, List, Dict
from utils.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """
    A service class responsible for managing connections and prompt matrices injected into the Gemini 1.5 Flash endpoint natively handling structured Pydantic payload generations.
    """
    def __init__(self) -> None:
        """
        Initializes the service by securely parsing and caching API keys and loading local mock structural event definitions from standard storage.

        Args:
            None

        Returns:
            None

        Raises:
            FileNotFoundError: If the mock_events.json mapping file is missing.
        """
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        with open("mock_events.json", "r") as f:
            self.mock_events = json.load(f)

    async def generate_itinerary(self, constraints: UserConstraints, distance_matrix_info: str, current_weather: Optional[str] = "Unknown") -> ItineraryResponse:
        """
        Calls the Gemini engine natively enforcing strict asynchronous schemas driven by distance paths and weather.

        Args:
            constraints (UserConstraints): The spatial and timeline definitions generated contextually.
            distance_matrix_info (str): The precalculated text string layout denoting coordinate transition delays.
            current_weather (Optional[str]): Current localized weather string parsed from upstream monitors.

        Returns:
            ItineraryResponse: A strictly mapped layout of sequence-based events bound to physical parameters.

        Raises:
            Exception: Managed internally; yields fallback itinerary upon consecutive failures.
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
        
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model='gemini-flash-latest',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ItineraryResponse,
                        temperature=0.0
                    )
                )
                return ItineraryResponse.model_validate_json(response.text)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}. Retrying in {base_delay}s...")
                    await asyncio.sleep(base_delay)
                    base_delay *= 2
                else:
                    logger.error(f"Gemini API failure after {max_retries} attempts: {e}")
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

    async def generate_staff_protocol(self, zone_id: str, alert_type: str) -> StaffActionResponse:
        """
        Generates an actionable staff protocol based on a specific zone and structural alert metric.

        Args:
            zone_id (str): The unique identifier for the targeted Zone (e.g. Zone B).
            alert_type (str): The categorical metric anomaly driving the alert (e.g. Crowd Density).

        Returns:
            StaffActionResponse: A strict Pydantic model defining the generated action protocol.

        Raises:
            RuntimeError: If the Gemini API fails entirely to generate the staff protocol.
        """
        prompt = f"""
        You are the Head of Event Security and Orchestration.
        An emergency/actionable alert has been triggered:
        - Zone: {zone_id}
        - Alert Type: {alert_type}
        
        Generate a concise, direct operational protocol for deployed staff to immediately resolve the situation. 
        Format your response to match the exact schema explicitly.
        """
        
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model='gemini-flash-latest',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=StaffActionResponse,
                        temperature=0.0
                    )
                )
                return StaffActionResponse.model_validate_json(response.text)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Gemini API attempt {attempt + 1} failed for protocol: {e}. Retrying in {base_delay}s...")
                    await asyncio.sleep(base_delay)
                    base_delay *= 2
                else:
                    logger.error(f"Gemini API failure after {max_retries} attempts generating protocol: {e}")
                    raise RuntimeError(f"Failed to generate staff protocol with Gemini API: {e}")

gemini_service = GeminiService()
