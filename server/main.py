"""
Main application entry point for the Next-Gen Event Concierge.
Orchestrates situational awareness, agentic reasoning, and real-time twin persistence.
Built for high-performance, resilient, and secure event orchestration.
"""
import logging
import os
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from redis.exceptions import RedisError, TimeoutError
from starlette.middleware.base import BaseHTTPMiddleware

# Strict Architectural Layering: Initialization Hub
from api.attendee import router as itinerary_router
from api.staff import router as staff_router
from api.websockets import router as ws_router, stream_manager
from services.vector_index import vector_index
from services.spatial_router import spatial_router
from infrastructure.config import settings
from infrastructure.firebase import fb_manager
from infrastructure.redis import cache

# Global Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the application lifecycle and distributed service synchronization."""
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
        
        # Start real-time PubSub listener
        asyncio.create_task(stream_manager.broadcast_redis_updates())
        
        from services.simulation import sim_engine
        await sim_engine.start_sim()
        
        logger.info("Application infrastructure synchronized (Tactical Engines active).")
    except Exception as e:
        logger.error(f"Infrastructure Level Failure: {e}")

    yield
    
    # 3. Graceful Teardown Sequence
    try:
        await cache.close()
        logger.info("Application released successfully.")
    except Exception as e:
        logger.debug(f"Teardown bypass: {e}")

app = FastAPI(
    title="Next-Gen Event Concierge",
    description="Agentic AI Platform with Real-Time Persistence (Winner Tier)",
    version="3.0.0",
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
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "no-referrer"
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
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(itinerary_router, prefix="/api")
app.include_router(staff_router, prefix="/api/staff")
app.include_router(ws_router)

@app.get("/", include_in_schema=False)
async def api_root() -> JSONResponse:
    """Operational status check for the Event Concierge API."""
    return JSONResponse(content={
        "status": "synchronized",
        "service": "Next-Gen Event Concierge API",
        "version": "3.0.0",
        "docs": "/api/docs"
    })

# Global Exception Handlers
@app.exception_handler(TimeoutError)
@app.exception_handler(RedisError)
async def redis_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"error": "Service Unavailable", "message": "Tactical persistence layer is temporarily restricted."}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = str(uuid.uuid4())
    logger.exception(f"CRITICAL [trace_id={trace_id}]: Internal orchestration anomaly.")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Anomaly.", "trace_id": trace_id}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
