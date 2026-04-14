from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
import os
from api.routes import router as itinerary_router
from utils.redis import cache
import uvicorn
from contextlib import asynccontextmanager
from redis.exceptions import TimeoutError, RedisError
import logging

logger = logging.getLogger(__name__)

from typing import AsyncGenerator

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Execute startup logic
    await cache.connect()
    yield
    # Execute shutdown logic
    await cache.close()

app = FastAPI(
    title="Context-Aware Event Concierge",
    description="API for time-optimized, conflict-free event itineraries.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(itinerary_router, prefix="/api")

@app.get("/", include_in_schema=False)
async def serve_index() -> FileResponse:
    return FileResponse(os.path.join("static", "index.html"))

@app.exception_handler(TimeoutError)
@app.exception_handler(RedisError)
async def redis_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Redis Connection Error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"error": "Service Unavailable", "message": "Cache/Database connection timeout."}
    )

@app.exception_handler(RuntimeError)
async def upstream_api_exception_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    logger.error(f"Upstream API Error (Maps/Gemini): {exc}")
    return JSONResponse(
        status_code=502,
        content={"error": "Bad Gateway", "message": "An upstream API failed to process the request."}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Internal Server Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred."}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
