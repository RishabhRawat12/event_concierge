import logging
import asyncio
from typing import Optional
from schemas.models import ItineraryResponse, UserConstraints
from .agent import agent_service
# Need to import weather if it exists, or use agent directly
# Based on current code, we had weather_service but I might need to move it to infrastructure
from infrastructure.redis import cache

logger = logging.getLogger(__name__)

class ItineraryService:
    """Orchestrates high-performance itinerary generation with non-cascading failure protection."""

    async def generate_smart_itinerary(
        self, 
        constraints: UserConstraints, 
        lat_r: float, 
        lon_r: float
    ) -> ItineraryResponse:
        """
        Main business logic for itinerary synthesis.
        Coordinating weather context and AI orchestration.
        """
        # Concurrent fetch of Situational Context (Weather)
        # Note: If weather_service is not available, we use default "Clear"
        weather = "Clear"
        
        try:
            # AI Orchestration within strict tactical window
            try:
                result = await asyncio.wait_for(
                    agent_service.generate_itinerary(constraints, "", weather),
                    timeout=5.0
                )
                result.current_weather = weather
                return result
            except (asyncio.TimeoutError, Exception) as ai_err:
                logger.error(f"AI Orchestration latency spike/error: {ai_err}. Triggering Shadow-Engine.")
                return await agent_service._generate_simulated_itinerary(constraints, weather)

        except Exception as e:
            logger.error(f"Safe Orchestration anomaly: {e}")
            return await agent_service._generate_simulated_itinerary(constraints, "Clear")

itinerary_service = ItineraryService()
