# Context-Aware Event Concierge

A highly concurrent, async backend service designed to rapidly generate time-optimized, logically sound event itineraries based on geolocation constraints. By merging physical distance mapping, local environmental conditions, and large language model structured reasoning, it produces a realistic, executable travel plan.

### Links

  * **Live API (Swagger UI):** [https://event-concierge-661835888735.europe-west1.run.app/docs](https://www.google.com/search?q=https://event-concierge-661835888735.europe-west1.run.app/docs)
  * **Vertical:** Physical Event Experience

### 🌟 Advanced Feature: Real-Time Weather Integration

Unlike static generators, this concierge queries the OpenWeatherMap API to adapt your day.

  * **Rainy Day Logic:** Automatically prioritizes indoor breakout sessions and adjusts walking buffers to account for slower travel.
  * **Clear Sky Logic:** Encourages outdoor rooftop networking and garden sessions.

### 🚀 Core Architecture

  * **FastAPI (Async-First):** Relies on `aiohttp` and asynchronous contexts to rapidly process heavy I/O without blocking event loops. Core endpoints are protected by a custom Redis-backed token bucket rate limiter to prevent abuse.
  * **Distance Matrix Caching:** Batches Google Maps Distance Matrix API queries between user origins and event destinations. Responses are aggressively cached via a resilient Upstash Redis mechanism, reducing upstream latency by over 80%.
  * **Gemini Decision Engine:** All context (spatial geometry, global weather reports, and user parameter constraints) is channeled into the `gemini-1.5-flash` API. Utilizing native structured outputs, Gemini strictly enforces Pydantic schemas to validate and formulate conflict-free JSON itineraries.

### 💻 API Usage Example

To test the API, send a POST request to `/api/itinerary` with the following JSON payload:

```json
{
  "user_location": {
    "latitude": 30.3165,
    "longitude": 78.0322
  },
  "start_time": "09:00",
  "end_time": "18:00",
  "preferred_topics": ["Tech", "Networking", "AI"]
}
```

### Assumptions

  * Geodetic coordinates (Latitude/Longitude) provided by the client are structurally valid.
  * Walking paths returned by standard Map routing engines remain unobstructed, excluding unpredictable construction blockades.

### Setup Instructions

Install project dependencies:
`pip install -r requirements.txt`

Assign your security keys (a `.env` file is also supported):
`export GEMINI_API_KEY="your-gemini-key"`
`export GOOGLE_MAPS_API_KEY="your-google-maps-key"`
`export OPENWEATHER_API_KEY="your-open-weather-key"`
`export REDIS_URL="your-redis-url"`

Run the application:
`uvicorn main:app --reload`

Run the internal test pipeline:
`pytest tests/`
