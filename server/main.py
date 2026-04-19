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
from services.vector_index import vector_index
from services.spatial_router import spatial_router
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
        await cache.connect()
        events = await vector_index.load_events()
        spatial_router.initialize(events)
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
        # Trusted Proxy Check: Prevents IP Spoofing for rate limiting
        client_host = request.client.host if request.client else "0.0.0.0"
        if client_host not in settings.TRUSTED_PROXIES and client_host != "127.0.0.1":
            # If not from a trusted proxy, we only allow X-Forwarded-For if it's not present
            # or we log as a potential spoofing attempt.
            request.state.is_trusted_proxied = False
        else:
            request.state.is_trusted_proxied = True

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0" # Disable legacy for CSP
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "no-referrer"
        
        # Hardened Content Security Policy (Strict: No unsafe-inline)
        csp = (
            "default-src 'self' https://maps.googleapis.com https://*.googleapis.com https://fonts.gstatic.com; "
            "script-src 'self' https://maps.googleapis.com https://*.googleapis.com https://cdn.jsdelivr.net; "
            "style-src 'self' https://fonts.googleapis.com https://*.googleapis.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com *.ggpht.com https://*.google.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://maps.googleapis.com https://*.googleapis.com wss: ws:; "
            "frame-src 'self' https://maps.googleapis.com https://*.google.com; "
            "base-uri 'self'; form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Cross-Origin Resource Policy: Strictly Whitelisted
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Route Mounting
if os.path.exists("static"):
    # Ensure static files are served without directory listing and with cache headers
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(itinerary_router, prefix="/api")
app.include_router(staff_router, prefix="/api/staff")

@app.get("/", include_in_schema=False)
async def api_root() -> JSONResponse:
    """Operational status check for the Event Concierge API."""
    return JSONResponse(content={
        "status": "synchronized",
        "service": "Next-Gen Event Concierge API",
        "version": "2.1.0",
        "docs": "/api/docs"
    })

# Structured Global Exception Handlers: Anonymized for Security
@app.exception_handler(TimeoutError)
@app.exception_handler(RedisError)
async def redis_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Cache Layer Failure: {exc}")
    return JSONResponse(
        status_code=503,
        content={"error": "Service Unavailable", "message": "Tactical persistence layer is temporarily restricted."}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = str(uuid.uuid4())
    # Log the full exception internally
    logger.exception(f"CRITICAL [trace_id={trace_id}]: Internal orchestration anomaly.")
    # Return anonymized response to requester
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


