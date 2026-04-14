import aiohttp
import logging
from utils.config import settings

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    async def get_current_weather(self, lat: float, lon: float) -> str:
        """
        Fetches the current weather main category (e.g., 'Clear', 'Rain', 'Snow', 'Clouds')
        from OpenWeatherMap based on latitude and longitude.
        """
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        weather_array = data.get("weather", [])
                        if weather_array:
                            return weather_array[0].get("main", "Clear")
                    logger.warning(f"Weather API returned non-200: {await response.text()}")
            except Exception as e:
                logger.error(f"Weather API request failed: {e}")
                
        return "Unknown"

weather_service = WeatherService()