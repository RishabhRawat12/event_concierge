import uuid
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError, TimeoutError

logger = logging.getLogger(__name__)

async def redis_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Infrastructure Failure (Redis): {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Service Unavailable: Coordination layer timeout."}
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = str(uuid.uuid4())
    logger.exception(f"Internal Error [TraceID: {trace_id}]")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "trace_id": trace_id
        }
    )

def setup_exception_handlers(app):
    app.add_exception_handler(TimeoutError, redis_exception_handler)
    app.add_exception_handler(RedisError, redis_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
