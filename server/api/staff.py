import logging
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.oauth2 import id_token # If using native google lib
from firebase_admin import auth
from infrastructure.firebase import fb_manager
from infrastructure.redis import cache
from schemas.models import StaffActionRequest, StaffActionResponse
from services.agent import agent_service

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(tags=["Staff Tactical Flow"])

async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Standardized Security: Native Firebase Admin SDK JWT verification."""
    try:
        # Native verification via firebase-admin
        decoded_token = auth.verify_id_token(credentials.credentials)
        return decoded_token
    except Exception as e:
        logger.warning(f"UNAUTHORIZED ACCESS ATTEMPT: {e}")
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Invalid or expired tactical token."
        )

@router.post("/zone-action", response_model=StaffActionResponse)
async def trigger_staff_action(
    request: StaffActionRequest, 
    decoded_token: dict = Depends(verify_firebase_token)
) -> StaffActionResponse:
    """
    [Staff Core] Orchestrates tactical personnel deployment.
    Publishes real-time state updates to Redis PubSub for zero-latency client sync.
    """
    try:
        # 1. Logic Layer: Protocol Synthesis
        protocol = await agent_service.generate_staff_protocol(request.zone_id, request.alert_type)
        
        # 2. Infrastructure: Real-time Persistence & Async PubSub
        update_payload = {
            "zone_id": request.zone_id,
            "alert_type": request.alert_type,
            "congestion": 85,
            "timestamp": "now"
        }
        
        # Push update to Redis PubSub channel
        await cache.publish("venue_updates", update_payload)
        
        return protocol
    except Exception as e:
        logger.error(f"Staff operational failure: {e}")
        raise HTTPException(status_code=500, detail="Staff service anomaly.")
