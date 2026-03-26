"""
Middleware: API key authentication and rate limiting.
"""

from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.config import get_settings

settings = get_settings()

# ── Rate Limiter ───────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── API Key Auth ───────────────────────────────────────────────
async def verify_api_key(request: Request):
    """
    Lightweight API key check.
    Pass the key via header: X-API-Key
    Skip auth for /api/health and /docs endpoints.
    """
    skip_paths = ["/api/health", "/docs", "/openapi.json", "/redoc"]
    if request.url.path in skip_paths:
        return

    api_key = request.headers.get("X-API-Key")
    # If no secret is configured, skip auth (dev mode)
    if settings.api_secret_key == "default-secret-key":
        return

    if not api_key or api_key != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
