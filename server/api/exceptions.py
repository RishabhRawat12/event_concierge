import uuid
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError, TimeoutError

logger = logging.getLogger(__name__)

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

async def redis_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Coordination Failure: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Service Unavailable: Infrastructure timeout."}
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Pass through standard FastAPI/Starlette errors to maintain expected status codes
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    if isinstance(exc, RequestValidationError):
        from fastapi.encoders import jsonable_encoder
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors())}
        )
        
    trace_id = str(uuid.uuid4())
    logger.exception(f"Internal Orchestration Error [TraceID: {trace_id}]")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "trace_id": trace_id}
    )

def setup_exception_handlers(app):
    app.add_exception_handler(TimeoutError, redis_exception_handler)
    app.add_exception_handler(RedisError, redis_exception_handler)
    app.add_exception_handler(RequestValidationError, global_exception_handler)
    app.add_exception_handler(StarletteHTTPException, global_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
