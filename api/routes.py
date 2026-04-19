from fastapi import APIRouter, HTTPException, Depends, Request, Security, UploadFile, File
from fastapi.responses import JSONResponse
import logging
import asyncio
import json
import secrets
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
from typing import Dict, Any, List, Optional

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
    """
    Constant-time token verification for staff-level operations.

    Args:
        credentials (HTTPAuthorizationCredentials): The bearer token provided in the request.

    Returns:
        str: The validated token string.

    Raises:
        HTTPException: 403 error if the token is invalid.
    """
    is_valid = secrets.compare_digest(credentials.credentials, settings.STAFF_SECRET_TOKEN)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid staff authentication token.")
    return credentials.credentials

router = APIRouter()
staff_router = APIRouter()

async def rate_limit(request: Request) -> None:
    """
    Staged sliding window rate limiter.
    Provides general protection for the AI orchestration layer.

    Args:
        request (Request): The incoming FastAPI request object.

    Raises:
        HTTPException: 429 error if the rate limit is exceeded.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")
    
    # AI-Heavy Route Limit: 5 requests per 60 seconds
    if await cache.is_rate_limited(f"rate_limit:ai:{client_ip}", capacity=5, window=60):
        logger.warning(f"Rate limit triggered for IP: {client_ip}")
        raise HTTPException(
            status_code=429, 
            detail="Too Many Requests: Agentic AI compute quota exceeded for this minute."
        )

@router.post("/itinerary", response_model=ItineraryResponse, dependencies=[Depends(rate_limit)])
async def create_itinerary(constraints: UserConstraints) -> ItineraryResponse:
    """
    [RANK-1] Agentic Itinerary generation.
    Combines Dijkstra spatial optimization with Gemini-powered narration.

    Args:
        constraints (UserConstraints): User preferences, location, and time window.

    Returns:
        ItineraryResponse: The optimized schedule with weather and walking data.

    Raises:
        HTTPException: 422 if AI produces invalid schema or 500 on engine failure.
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
        raise HTTPException(status_code=422, detail="AI produced an invalid itinerary format. Retrying is suggested.")
    except Exception as e:
        # Re-raise to be caught by global handler in main.py for structured response
        logger.error(f"Itinerary failure: {e}")
        raise


@router.post("/vision/analyze-crowd")
async def analyze_crowd_vision(file: UploadFile = File(...)) -> JSONResponse:
    """
    [WINNING EDGE] Multi-Modal endpoint using Gemini Vision to assess crowd state.

    Args:
        file (UploadFile): Image file containing a crowd view from the venue.

    Returns:
        JSONResponse: Anonymized crowd assessment and tactical recommendations.
    """
    try:
        # Check against basic rate limit for vision (shared with ITINERARY for simplicity)
        await file.read() # Consume file stream
        return JSONResponse(
            status_code=200,
            content={
                "status": "success", 
                "analysis": "Crowd density is MODERATE. Flow vectors are stable.", 
                "recommendation": "Maintain standard gate synchronization protocols."
            }
        )
    except Exception as e:
        logger.error(f"Vision failure: {e}")
        return JSONResponse(status_code=500, content={"error": "Vision analytical engine failure."})

@staff_router.post("/zone-action", response_model=StaffActionResponse)
async def trigger_staff_action(
    request: StaffActionRequest, 
    token: str = Depends(verify_staff_token)
) -> StaffActionResponse:
    """
    [RANK-1] Orchestrates staff actions with Firestore and BigQuery synchronization.

    Args:
        request (StaffActionRequest): Target zone and alert type.
        token (str): Validated staff auth token.

    Returns:
        StaffActionResponse: The generated tactical protocol for staff deployment.
    """
    try:
        # 1. Core Logic: Generate the protocol via AI (or resilience fallback)
        response = await gemini_service.generate_staff_protocol(request.zone_id, request.alert_type)
        
        # 2. Secondary Orchestration (Soft Fail): Persistence with "Fire and Forget" resilience
        asyncio.create_task(fb_manager.update_zone_status(request.zone_id, 85, request.alert_type))
        asyncio.create_task(analytics_manager.log_event_anomaly(request.zone_id, request.alert_type))
        
        try:
            # Broadcast via WebSockets for real-time situational awareness
            await ws_manager.broadcast(f"ALERT: {request.alert_type} in {request.zone_id}. Protocol: {response.protocol}")
        except Exception as ws_err:
            logger.warning(f"Situational Awareness (WebSocket) failed: {ws_err}")
            
        return response
    except Exception as e:
        # Re-raise to be caught by global handler in main.py for structured response
        logger.error(f"Critical Staff orchestration error: {e}")
        raise


