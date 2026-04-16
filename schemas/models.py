from pydantic import BaseModel, Field, StringConstraints
from typing import List, Optional, Annotated

class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude of the location")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude of the location")

class UserConstraints(BaseModel):
    user_location: Coordinates
    start_time: str = Field(..., pattern=r"^\d{1,2}:\d{2} [AP]M$", description="Start time (e.g. 10:00 AM)")
    end_time: str = Field(..., pattern=r"^\d{1,2}:\d{2} [AP]M$", description="End time (e.g. 05:00 PM)")
    preferred_topics: List[Annotated[str, StringConstraints(min_length=2, max_length=50)]] = Field(..., min_length=1)

class Event(BaseModel):
    event_name: str = Field(..., description="Name of the chosen event from the static mock events list")
    start_time: str = Field(..., description="Start time formatted appropriately (e.g. 10:00 AM)")
    end_time: str = Field(..., description="End time formatted appropriately (e.g. 11:30 AM)")
    walking_directions: str = Field(..., description="Brief summary of how to get there based on the location")
    transition_time_seconds: int = Field(..., description="Allocated transition time in seconds based on Maps API distance matrix")

class ItineraryResponse(BaseModel):
    current_weather: Optional[str] = Field(default=None, description="The prevailing weather during the itinerary calculation")
    itinerary: List[Event] = Field(..., description="Ordered list of events forming the optimal, conflict-free itinerary")

class StaffActionRequest(BaseModel):
    zone_id: str = Field(..., description="The unique identifier for the targeted Zone (e.g. Zone B)")
    alert_type: str = Field(..., description="The categorical metric anomaly driving the alert (e.g. Crowd Density)")

class StaffActionResponse(BaseModel):
    protocol: str = Field(..., description="The AI-orchestrated response protocol for personnel deployment")
