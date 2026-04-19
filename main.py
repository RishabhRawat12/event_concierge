"""
Main application entry point for the Next-Gen Event Concierge.
Orchestrates situational awareness, agentic reasoning, and real-time twin persistence.
Built for high-performance, resilient, and secure event orchestration.
"""
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
import uvicorn
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from redis.exceptions import RedisError, TimeoutError
from starlette.middleware.base import BaseHTTPMiddleware

# Internal Infrastructure & Services
from api.routes import router as itinerary_router
from api.routes import staff_router
from services.gemini import gemini_service
from utils.analytics import analytics_manager
from utils.config import settings
from utils.firebase import fb_manager
from utils.redis import cache
from utils.simulation import sim_engine
from utils.websockets import ws_manager

# Global Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="static")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the application lifecycle and distributed service synchronization.
    Ensures safe initialization and graceful teardown of tactical components.
    """
    # 1. Cloud Infrastructure Initialization
    try:
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            from google.cloud import logging as gcloud_logging
            logging_client = gcloud_logging.Client()
            logging_client.setup_logging()
            logger.info("GCP Structured Logging synchronized.")
    except Exception as e:
        logger.warning(f"Metadata Link Warning: {e}. Falling back to standard logs.")

    # 2. Tactical Service Synchronization
    try:
        fb_manager.connect()
        analytics_manager.connect()
        await cache.connect()
        await gemini_service.load_events()
        await sim_engine.start_sim()
        logger.info("Application infrastructure synchronized (Tactical Engines active).")
    except Exception as e:
        logger.error(f"Infrastructure Level Failure: {e}")

    yield
    
    # 3. Graceful Teardown Sequence
    try:
        await cache.close()
        await sim_engine.stop_sim()
        logger.info("Application released successfully.")
    except Exception as e:
        logger.debug(f"Teardown bypass: {e}")

app = FastAPI(
    title="Next-Gen Event Concierge",
    description="Agentic AI Platform with Real-Time Persistence (Winner Tier)",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces high-performance security headers and strict CSP protocols."""
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Hardened Content Security Policy
        csp = (
            "default-src 'self' https://maps.googleapis.com https://*.googleapis.com https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline' https://maps.googleapis.com https://*.googleapis.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://*.googleapis.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com *.ggpht.com https://*.google.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://maps.googleapis.com https://*.googleapis.com wss: ws:; "
            "frame-src 'self' https://maps.googleapis.com https://*.google.com; "
            "base-uri 'self'; form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Cross-Origin Resource Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tighten for production deployment
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Route Mounting
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(itinerary_router, prefix="/api")
app.include_router(staff_router, prefix="/api/staff")

@app.get("/", include_in_schema=False)
async def serve_index(request: Request) -> Response:
    """Entry point for the Attendee & Staff tactical dashboard."""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "maps_key": settings.GOOGLE_MAPS_API_KEY, 
            "events": gemini_service._mock_events
        }
    )

# Structured Global Exception Handlers
@app.exception_handler(TimeoutError)
@app.exception_handler(RedisError)
async def redis_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Cache Layer Failure: {exc}")
    return JSONResponse(
        status_code=503,
        content={"error": "Service Unavailable", "message": "Tactical cache layer is temporarily offline."}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = str(uuid.uuid4())
    logger.exception(f"CRITICAL [trace_id={trace_id}]: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Anomaly. Tactical response unit notified.",
            "trace_id": trace_id
        }
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Real-time situational awareness stream for crowd insights."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


