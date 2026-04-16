from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time
import uuid
from contextlib import asynccontextmanager
from redis.exceptions import TimeoutError, RedisError
import logging
import aiohttp
from typing import AsyncGenerator
from fastapi.templating import Jinja2Templates
import uvicorn

from api.routes import router as itinerary_router, staff_router
from utils.redis import cache
from utils.websockets import ws_manager
from services.weather import weather_service
from services.gemini import gemini_service
from utils.config import settings

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="static")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Execute startup logic safely to prevent Cloud Run boot crashes
    try:
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_CLOUD_PROJECT"):
            import google.cloud.logging  # type: ignore
            gcloud_logging_client = google.cloud.logging.Client()
            gcloud_logging_client.setup_logging()
    except Exception:
        pass

    try:
        await cache.connect()
    except Exception as e:
        logger.error(f"Failed to connect to Redis during startup: {e}")
        
    await gemini_service.load_events()
    weather_service.session = aiohttp.ClientSession()
        
    yield
    
    # Execute shutdown logic
    if getattr(weather_service, 'session', None):
        await weather_service.session.close()
        
    try:
        await cache.close()
    except Exception:
        pass

app = FastAPI(
    title="Context-Aware Event Concierge",
    description="API for time-optimized, conflict-free event itineraries.",
    version="1.0.0",
    lifespan=lifespan
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        # Hardened CSP for production: allows maps, fonts, and specific external workers/frames
        # Added exceptions for Swagger UI (Docs) dependencies
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' https://maps.googleapis.com https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline' https://maps.googleapis.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com *.ggpht.com https://fastapi.tiangolo.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://maps.googleapis.com wss: ws:; "
            "worker-src 'self' blob:; "
            "frame-src 'self' https://maps.googleapis.com; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"], # Tighten to local dev port
    allow_credentials=True,
    allow_methods=["GET", "POST"], # Tighten methods
    allow_headers=["*"],
)

app.include_router(itinerary_router, prefix="/api")
app.include_router(staff_router, prefix="/api/staff", tags=["Staff Action Orchestration"])

@app.get("/", include_in_schema=False)
async def serve_index(request: Request) -> Response:
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "maps_key": settings.GOOGLE_MAPS_API_KEY, "events": gemini_service.mock_events}
    )

@app.exception_handler(TimeoutError)
@app.exception_handler(RedisError)
async def redis_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Redis Connection Error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"error": "Service Unavailable", "message": "Cache/Database connection timeout."},
        headers={"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY"}
    )

@app.exception_handler(RuntimeError)
async def upstream_api_exception_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    logger.error(f"Upstream API Error (Maps/Gemini): {exc}")
    return JSONResponse(
        status_code=502,
        content={"error": "Bad Gateway", "message": "An upstream API failed to process the request."},
        headers={"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY"}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = str(uuid.uuid4())
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    logger.error(f"trace_id={trace_id} | Internal Server Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error",
            "trace_id": trace_id,
            "timestamp": timestamp
        },
        headers={"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY"}
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
