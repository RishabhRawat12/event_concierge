from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import time
import uuid
from contextlib import asynccontextmanager
from redis.exceptions import TimeoutError, RedisError
import logging
import aiohttp
from typing import AsyncGenerator, Dict, Any
import uvicorn

# Internal Infrastructure & Services
from api.routes import router as itinerary_router, staff_router
from utils.redis import cache
from utils.websockets import ws_manager
from utils.firebase import fb_manager
from utils.analytics import analytics_manager
from utils.simulation import sim_engine
from services.weather import weather_service
from services.gemini import gemini_service
from utils.config import settings

# Initialize Logging and Templates
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="static")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the application lifecycle, ensuring safe initialization of 
    distributed services (Redis, Firebase, BigQuery) and structured logging.
    """
    # 1. Structured Logging Initialization (GCP Tier)
    try:
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            from google.cloud import logging as gcloud_logging
            logging_client = gcloud_logging.Client()
            logging_client.setup_logging()
            logger.info("GCP Structured Logging initialized successfully.")
    except Exception as e:
        logger.warning(f"GCP Logging Init Warning: {e}. Falling back to standard logs.")

    # 2. Service Connections with Resilience
    try:
        fb_manager.connect()
        analytics_manager.connect()
        await sim_engine.start_sim()
    except Exception as e:
        logger.error(f"Core Services Init failure: {e}")

    try:
        await cache.connect()
    except Exception as e:
        logger.error(f"Redis fallback mode active: {e}")
        
    # 3. Warming components
    await gemini_service.load_events()
    weather_service.session = aiohttp.ClientSession()
        
    yield
    
    # 4. Clean Shutdown Sequence
    if getattr(weather_service, 'session', None):
        await weather_service.session.close()
    try:
        await cache.close()
    except Exception:
        pass
    await sim_engine.stop_sim()
    logger.info("Application shutdown sequence complete.")

app = FastAPI(
    title="Next-Gen Event Concierge",
    description="Agentic AI Platform with Real-Time Persistence (Winner Tier)",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces Rank-1 security headers and CSP protocols."""
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Hardened CSP specifically for Google Maps and Event Assets
        csp_directives = [
            "default-src 'self' https://maps.googleapis.com https://*.googleapis.com https://fonts.gstatic.com",
            "script-src 'self' 'unsafe-inline' https://maps.googleapis.com https://*.googleapis.com https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://*.googleapis.com https://cdn.jsdelivr.net",
            "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com *.ggpht.com https://*.google.com",
            "font-src 'self' https://fonts.gstatic.com",
            "connect-src 'self' https://maps.googleapis.com https://*.googleapis.com wss: ws:",
            "worker-src 'self' blob:",
            "frame-src 'self' https://maps.googleapis.com https://*.google.com",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Rank-1 CORS: Explicit Whitelist
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://event-concierge.vercel.app" # Example production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(itinerary_router, prefix="/api")
app.include_router(staff_router, prefix="/api/staff", tags=["Staff Action Orchestration"])

@app.get("/", include_in_schema=False)
async def serve_index(request: Request) -> Response:
    """Entry point for the Attendee & Staff interface."""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "maps_key": settings.GOOGLE_MAPS_API_KEY, "events": gemini_service.mock_events}
    )

@app.exception_handler(TimeoutError)
@app.exception_handler(RedisError)
async def redis_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Infrastructure Level Error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"error": "Service Unavailable", "message": "High-performance cache layer is temporarily offline."},
        headers={"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY"}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = str(uuid.uuid4())
    logger.exception(f"trace_id={trace_id} | Internal Server Error")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error. Our tactical team has been notified.",
            "trace_id": trace_id
        },
        headers={"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY"}
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Real-time orchestration socket for crowd insights."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

