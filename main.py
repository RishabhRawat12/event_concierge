from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os
import time
import uuid
from api.routes import router as itinerary_router, staff_router
from utils.redis import cache
import uvicorn
from contextlib import asynccontextmanager
from redis.exceptions import TimeoutError, RedisError
import logging

logger = logging.getLogger(__name__)

from typing import AsyncGenerator

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Execute startup logic safely to prevent Cloud Run boot crashes
    try:
        import google.cloud.logging  # type: ignore
        gcloud_logging_client = google.cloud.logging.Client()
        gcloud_logging_client.setup_logging()
    except Exception as e:
        logger.warning(f"Failed to initialize genuine Google Cloud Logging client: {e}")

    try:
        await cache.connect()
    except Exception as e:
        logger.error(f"Failed to connect to Redis during startup: {e}")
        
    yield
    
    # Execute shutdown logic
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
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(itinerary_router, prefix="/api")
app.include_router(staff_router, prefix="/api/staff", tags=["Staff Action Orchestration"])

@app.get("/", include_in_schema=False)
async def serve_index() -> FileResponse:
    return FileResponse(os.path.join("static", "index.html"))

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
