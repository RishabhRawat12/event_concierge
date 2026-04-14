from pydantic import BaseModel, Field
from typing import List, Optional

class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude of the location")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude of the location")

class UserConstraints(BaseModel):
    user_location: Coordinates
    start_time: str = Field(..., description="Start time in ISO format or descriptive string")
    end_time: str = Field(..., description="End time in ISO format or descriptive string")
    preferred_topics: List[str] = Field(..., description="List of preferred topics (e.g. AI, Cloud, Startups)")

class Event(BaseModel):
    event_name: str = Field(..., description="Name of the chosen event from the static mock events list")
    start_time: str = Field(..., description="Start time formatted appropriately (e.g. 10:00 AM)")
    end_time: str = Field(..., description="End time formatted appropriately (e.g. 11:30 AM)")
    walking_directions: str = Field(..., description="Brief summary of how to get there based on the location")
    transition_time_seconds: int = Field(..., description="Allocated transition time in seconds based on Maps API distance matrix")

class ItineraryResponse(BaseModel):
    current_weather: Optional[str] = Field(default=None, description="The prevailing weather during the itinerary calculation")
    itinerary: List[Event] = Field(..., description="Ordered list of events forming the optimal, conflict-free itinerary")
