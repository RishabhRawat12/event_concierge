from fastapi import APIRouter, HTTPException, Depends, Request, Security
import logging

logger = logging.getLogger(__name__)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas.models import UserConstraints, ItineraryResponse, StaffActionRequest, StaffActionResponse
from services.maps import maps_service
from services.gemini import gemini_service
from services.weather import weather_service
from utils.redis import cache
from utils.websockets import ws_manager
from utils.config import settings
import asyncio
import json

security = HTTPBearer()

def verify_staff_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    # Use environment-based token for better security
    if credentials.credentials != settings.STAFF_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid staff authentication token.")
    return credentials.credentials

router = APIRouter()

async def rate_limit(request: Request) -> None:
    """
    Validates sliding window logic via the Redis Cache connection to rate limit inbound API queries.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # Using 10 requests per 60 seconds
    is_limited = await cache.is_rate_limited(f"rate_limit:{client_ip}", capacity=10, window=60)
    if is_limited:
        raise HTTPException(status_code=429, detail="Too Many Requests - Rate limit exceeded")

@router.post("/itinerary", response_model=ItineraryResponse, dependencies=[Depends(rate_limit)])
async def create_itinerary(constraints: UserConstraints) -> ItineraryResponse:
    """
    Endpoint that processes physical geolocations, local weather states, and spatial distances to infer
    a logically sequenced event itinerary via GenAI endpoints.
    """
    try:
        # Filter mock events by topics
        topics_lower = [t.lower() for t in constraints.preferred_topics]
        filtered_events = [e for e in gemini_service.mock_events if e['topic'].lower() in topics_lower]
        
        # Fallback to all events if no topic matches to prevent empty matrix
        if not filtered_events:
            filtered_events = gemini_service.mock_events

        # Build distance matrix (from User -> Events, and Event -> Event)
        locations = [{
            "id": "user", 
            "name": "User Start Point", 
            "latitude": constraints.user_location.latitude, 
            "longitude": constraints.user_location.longitude
        }]
        
        for e in filtered_events:
            locations.append({
                "id": e["id"], 
                "name": e["name"], 
                "latitude": e["latitude"], 
                "longitude": e["longitude"]
            })

        distances = []
        try:
            # Gather all combinations with exactly one Maps API call
            matrix_dict = await maps_service.get_walking_time(locations, locations)
            
            for i in range(len(locations)):
                for j in range(len(locations)):
                    if i != j:
                        loc_i = locations[i]
                        loc_j = locations[j]
                        key = f"{loc_i['latitude']},{loc_i['longitude']}|{loc_j['latitude']},{loc_j['longitude']}"
                        if key in matrix_dict:
                            distances.append(f"From {loc_i['name']} to {loc_j['name']}: {matrix_dict[key]} seconds walking")
        except Exception as e:
            logger.warning(f"Resilient fallback for map error: {e}")
            pass

        matrix_info = "\n".join(distances)
        if not matrix_info:
            matrix_info = "Distance matrix unavailable. Assume average 600 seconds walking between any two points."

        # Fetch Weather Context
        current_weather = "Clear"
        try:
            current_weather = await weather_service.get_current_weather(
                lat=constraints.user_location.latitude,
                lon=constraints.user_location.longitude
            )
        except Exception:
            pass
        
        # Call Gemini Decision Engine
        itinerary = await gemini_service.generate_itinerary(constraints, matrix_info, current_weather)
        itinerary.current_weather = current_weather
        return itinerary

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_itinerary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

staff_router = APIRouter()

@staff_router.post("/zone-action", response_model=StaffActionResponse, dependencies=[Depends(verify_staff_token)])
async def trigger_staff_action(request: StaffActionRequest) -> StaffActionResponse:
    """
    Triggers an emergency or actionable alert context for staff to resolve based on GenAI metrics.
    """
    try:
        response = await gemini_service.generate_staff_protocol(request.zone_id, request.alert_type)
        
        # Dispatch the AI resolution instantly across all connected administrative UI tunnels (WebSockets)
        await ws_manager.broadcast(json.dumps({
            "zone_id": request.zone_id,
            "alert_type": request.alert_type,
            "protocol": response.protocol
        }))
        
        return response
    except Exception as e:
        logger.error(f"Error in trigger_staff_action: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while generating staff protocol.")
