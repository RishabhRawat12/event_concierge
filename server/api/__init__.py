from .attendee import router
from .staff import router as staff_router
from .websockets import router as ws_router

__all__ = ["router", "staff_router", "ws_router"]
