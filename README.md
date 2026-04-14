# Context-Aware Event Concierge

A highly concurrent, async backend service designed to rapidly generate time-optimized, logically sound event itineraries based on geolocation constraints.

## Vertical
Physical Event Experience

## Approach and Logic
- **FastAPI for High Concurrency:** The core framework is completely async-first, relying on `aiohttp` and native asynchronous context management to process heavy I/O workflows without blocking event loops.
- **Redis Caching:** We batch query the Google Maps Distance Matrix API to pre-load distance and walking times between user origin points and target events. We aggressively cache these matrix results via an Upstash Cloud Redis connection, massively reducing latency for subsequent overlapping geographical requests.
- **Gemini API:** We route the validated distances, mocked point of interest event locations, and the user's preferred topics into the Gemini API. Using native structured Pydantic outputs, Gemini computes the optimal layout and returns a conflict-free itinerary formatted strictly as guaranteed JSON.

## Assumptions
- We assume that the user provides valid geographical coordinates upon requesting an itinerary.
- We assume that the standard venue walking paths mapped by the Distance API remain valid and ignore random physical bottlenecks (e.g., temporary construction blockades).

## Setup Instructions
1. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Assign your security keys (a `.env` file is also supported):
   ```bash
   export GEMINI_API_KEY="your-key"
   export GOOGLE_MAPS_API_KEY="your-key"
   export REDIS_URL="your-redis-url"
   ```
3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```
4. Run the internal test pipeline:
   ```bash
   pytest tests/
   ```
