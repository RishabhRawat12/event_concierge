import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from schemas.models import ItineraryResponse, UserConstraints
from services.itinerary_service import itinerary_service
from infrastructure.redis import cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Attendee Flow"])

async def attendee_rate_limit(request: Request) -> None:
    """Standardized Validation: Rate limit attendee requests."""
    ip = request.client.host if request.client else "0.0.0.0"
    if await cache.is_rate_limited(f"ratelimit:attendee:{ip}", capacity=settings.ATTENDEE_RATE_LIMIT_CAPACITY, window=60):
        raise HTTPException(status_code=429, detail="Attendee quota exhausted.")

@router.post("/itinerary", response_model=ItineraryResponse, dependencies=[Depends(attendee_rate_limit)])
async def create_itinerary(constraints: UserConstraints) -> ItineraryResponse:
    """
    [Attendee Flow] Entry point for itinerary synthesis.
    Strictly follows Architectural Layering: Route -> Service -> Infrastructure.
    """
    try:
        lat_r, lon_r = round(constraints.user_location.latitude, 4), round(constraints.user_location.longitude, 4)
        
        # 1. Caching Layer (Infrastructure call)
        cache_key = f"itinerary:{lat_r}:{lon_r}:{hash(str(constraints.preferred_topics))}"
        
        result = await cache.get_or_compute(
            cache_key,
            itinerary_service.generate_smart_itinerary,
            ttl=300,
            constraints=constraints,
            lat_r=lat_r,
            lon_r=lon_r
        )
        return result
    except Exception as e:
        logger.error(f"Attendee itinerary orchestration failure: {e}")
        raise HTTPException(status_code=500, detail="Service link failure.")
