from fastapi import FastAPI
from api.routes import router as itinerary_router
from utils.redis import cache
import uvicorn
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
