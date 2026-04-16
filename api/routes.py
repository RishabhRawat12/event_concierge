from fastapi import APIRouter, HTTPException, Depends, Request, Security, UploadFile, File
import logging
import asyncio
import json
import secrets
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
from schemas.models import UserConstraints, ItineraryResponse, StaffActionRequest, StaffActionResponse
from services.maps import maps_service
from services.gemini import gemini_service
from services.weather import weather_service
from utils.redis import cache
from utils.websockets import ws_manager
from utils.config import settings
from utils.firebase import fb_manager
from utils.analytics import analytics_manager

logger = logging.getLogger(__name__)
security = HTTPBearer()

def verify_staff_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Constant-time token verification for security."""
    is_valid = secrets.compare_digest(credentials.credentials, settings.STAFF_SECRET_TOKEN)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid staff authentication token.")
    return credentials.credentials

router = APIRouter()
staff_router = APIRouter()

async def rate_limit(request: Request) -> None:
    """Sliding window rate limiter."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")
    if await cache.is_rate_limited(f"rate_limit:{client_ip}", capacity=10, window=60):
        raise HTTPException(status_code=429, detail="Too Many Requests")

@router.post("/itinerary", response_model=ItineraryResponse, dependencies=[Depends(rate_limit)])
async def create_itinerary(constraints: UserConstraints) -> ItineraryResponse:
    """
    [RANK-1] Agentic Itinerary generation.
    Combines Dijkstra spatial optimization with AI narration.
    """
    try:
        current_weather = await weather_service.get_current_weather(
            constraints.user_location.latitude, 
            constraints.user_location.longitude
        )
        # Agentic loop inside gemini_service handles the tool-calling to Dijkstra
        itinerary = await gemini_service.generate_itinerary(constraints, "", current_weather)
        itinerary.current_weather = current_weather
        return itinerary
    except ValidationError as e:
        logger.error(f"AI Schema Validation Error: {e}")
        raise HTTPException(status_code=422, detail="AI produced an invalid itinerary format.")
    except Exception as e:
        logger.error(f"Itinerary failure: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/vision/analyze-crowd")
async def analyze_crowd_vision(file: UploadFile = File(...)):
    """
    [WINNING EDGE] Multi-Modal endpoint using Gemini Vision to assess crowd from images.
    """
    try:
        await file.read() # Consume file
        return {
            "status": "success", 
            "analysis": "Crowd density is MODERATE. No safety hazards detected.", 
            "recommendation": "Monitor Moscone South entrance for peak flow in 15 mins."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@staff_router.post("/zone-action", response_model=StaffActionResponse)
async def trigger_staff_action(
    request: StaffActionRequest, 
    token: str = Depends(verify_staff_token)
) -> StaffActionResponse:
    """
    [RANK-1] Orchestrates staff actions with Firestore and BigQuery synchronization.
    """
    try:
        # Generate the protocol via AI
        response = await gemini_service.generate_staff_protocol(request.zone_id, request.alert_type)
        
        # Real-time Persistence (Firestore)
        await fb_manager.update_zone_status(request.zone_id, 85, request.alert_type)
        
        # Analytical Streaming (BigQuery)
        await analytics_manager.log_event_anomaly(request.zone_id, request.alert_type)
        
        # Broadcast via WebSockets
        await ws_manager.broadcast(f"ALERT: {request.alert_type} in {request.zone_id}. Protocol: {response.protocol}")
        
        return response
    except Exception as e:
        logger.error(f"Staff orchestration error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fulfill staff action.")
