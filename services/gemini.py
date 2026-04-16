import json
import logging
import asyncio
import aiofiles
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
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.mock_events = []

    async def load_events(self) -> None:
        """
        Loads mock events asynchronously during application startup.
        """
        try:
            async with aiofiles.open("mock_events.json", mode="r") as f:
                content = await f.read()
                self.mock_events = json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load mock events: {e}")
            self.mock_events = []

    def _sanitize_input(self, text: str) -> str:
        """
        Protects against prompt injection by stripping potential control delimiters.
        """
        if not text:
            return ""
        # Remove common delimiters used in injection attacks
        forbidden = ["```", "---", "###", "<script>", "prompt:"]
        sanitized = text
        for f in forbidden:
            sanitized = sanitized.replace(f, "")
        return sanitized[:500] # Hard limit for safety

    async def generate_itinerary(self, constraints: UserConstraints, distance_matrix_info: str, current_weather: Optional[str] = "Unknown") -> ItineraryResponse:
        """
        Calls the Gemini engine natively enforcing strict asynchronous schemas driven by distance paths and weather.
        """        
        # Sanitize all inputs from external or untrusted sources
        clean_weather = self._sanitize_input(current_weather)
        clean_matrix = self._sanitize_input(distance_matrix_info)
        clean_topics = [self._sanitize_input(t) for t in constraints.preferred_topics]

        prompt = f"""
        You are an expert Context-Aware Event Concierge. Your task is to generate a time-optimized, conflict-free itinerary.
        The user has provided the following constraints:
        - User Start Location: Lat: {constraints.user_location.latitude}, Lng: {constraints.user_location.longitude}
        - Time Window: {constraints.start_time} to {constraints.end_time}
        - Preferred Topics: {', '.join(clean_topics)}
        
        Weather Context:
        The current weather is '{clean_weather}'.
        If the weather is 'Rain', 'Snow', or 'Storm', prioritize indoor events from the mock list and increase the transition_time_seconds for walking by 50%.
        If the weather is 'Clear', prioritize outdoor networking sessions.

        Here are the available mocked events:
        {json.dumps(self.mock_events, indent=2)}

        Here is the relevant distance matrix showing walking times in seconds between these locations:
        {clean_matrix}
        
        Using ONLY the provided events, select the most relevant events based on the user's topics.
        Ensure that the event times do not overlap and that the user has enough transition time (based on the distance matrix) to walk from one event to the next.
        Return the itinerary as strict JSON conforming exactly to the requested schema.
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
                    logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}. Retrying...")
                    await asyncio.sleep(base_delay * (2 ** attempt))
                else:
                    logger.error(f"Gemini API failure after {max_retries} attempts: {e}")
                    return ItineraryResponse(
                        itinerary=[
                            Event(
                                event_name="AI & Future of Work Keynote (Fallback)",
                                start_time="09:00 AM",
                                end_time="10:00 AM",
                                walking_directions="Proceed to the main hall.",
                                transition_time_seconds=300
                            )
                        ]
                    )

    async def generate_staff_protocol(self, zone_id: str, alert_type: str) -> StaffActionResponse:
        """
        Generates an actionable staff protocol based on a specific zone and structural alert metric.
        """
        clean_zone = self._sanitize_input(zone_id)
        clean_alert = self._sanitize_input(alert_type)

        prompt = f"""
        You are the Head of Event Security and Orchestration.
        An emergency/actionable alert has been triggered:
        - Zone: {clean_zone}
        - Alert Type: {clean_alert}
        
        Generate a concise, direct operational protocol for deployed staff to immediately resolve the situation. 
        Format your response to match the exact schema explicitly.
        """
        
        max_retries = 3
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
                    await asyncio.sleep(1.0 * (2 ** attempt))
                else:
                    logger.error(f"Gemini API failure: {e}")
                    raise RuntimeError(f"Failed to generate staff protocol: {e}")

gemini_service = GeminiService()
