from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from infrastructure.config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces standard security headers."""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Standard CSP for a React/FastAPI stack
        csp_parts = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-eval' https://maps.googleapis.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com",
            "font-src 'self' https://fonts.gstatic.com",
            "connect-src 'self' https://*.googleapis.com ws: wss:",
            "frame-src 'self' https://*.google.com"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_parts)
        return response
