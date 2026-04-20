import logging
import os
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.attendee import router as attendee_router
from api.staff import router as staff_router
from api.websockets import router as ws_router, stream_manager
from api.middleware import SecurityHeadersMiddleware
from api.exceptions import setup_exception_handlers

from infrastructure.config import settings
from infrastructure.firebase import fb_manager
from infrastructure.redis import cache
from services.vector_index import vector_index
from services.spatial_router import spatial_router

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages system-wide resource initialization and teardown."""
    try:
        # Initialize Core Infrastructure
        fb_manager.connect()
        await cache.connect()
        
        # Initialize Application Services
        events = await vector_index.load_events()
        spatial_router.initialize(events)
        
        # Start background tasks
        asyncio.create_task(stream_manager.broadcast_redis_updates())
        
        from services.simulation import sim_engine
        await sim_engine.start_sim()
        
        logger.info("System operational: All services synchronized.")
    except Exception as e:
        logger.critical(f"Startup sequence failed: {e}")

    yield
    
    await cache.close()
    logger.info("System shutdown complete.")

app = FastAPI(
    title="Event Concierge Service",
    description="Real-time venue orchestration with Vertex AI grounding.",
    version="3.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middleware Setup
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Router Mounting
app.include_router(attendee_router, prefix="/api")
app.include_router(staff_router, prefix="/api/staff")
app.include_router(ws_router)

# Exception Handlers
setup_exception_handlers(app)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def api_root():
    return {"status": "synchronized", "service": "Event Concierge API"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "3.1.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
