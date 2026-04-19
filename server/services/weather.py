"""
OpenWeatherMap integration for situational metereological awareness.
Provides real-time weather context to the agentic orchestration engine.
"""
import logging
import httpx
from utils.config import settings

logger = logging.getLogger(__name__)

class WeatherService:
    """Orchestrates authenticated weather queries via OpenWeatherMap API."""

    def __init__(self) -> None:
        self._api_key: str = settings.OPENWEATHER_API_KEY
        self._base_url: str = "https://api.openweathermap.org/data/2.5/weather"

    async def get_current_weather(self, lat: float, lon: float) -> str:
        """
        Fetches a tactical weather summary for the given coordinates.

        Args:
            lat: Latitude of the observation point.
            lon: Longitude of the observation point.

        Returns:
            A concise description of the current weather (e.g. 'Clear').
            Defaults to 'Unknown' if the API is unreachable or fails.
        """
        if not self._api_key:
            return "Unknown"

        params = {
            "lat": str(lat),
            "lon": str(lon),
            "appid": self._api_key,
            "units": "metric"
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self._base_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    main = data.get("weather", [{}])[0].get("main", "Clear")
                    temp = data.get("main", {}).get("temp", "?")
                    logger.debug(f"Weather context synchronized: {main} ({temp}°C)")
                    return f"{main} ({temp}°C)"
                
                logger.warning(f"Weather API returned non-200: {resp.status_code}")
                return "Unknown"
        except (httpx.HTTPError, KeyError, IndexError) as e:
            logger.warning(f"Weather Engine synchronization failed: {e}. Defaulting to Unknown.")
            return "Unknown"

weather_service = WeatherService()