import time
from collections import defaultdict
from fastapi import Header, HTTPException, Request
from src.config import Settings
from src.core.security import verify_api_key

settings = Settings()

ip_requests: dict[str, list[float]] = defaultdict(list)
global_requests: list[float] = []

def _is_allowed(buckets: list[float], window_seconds: int, max_requests: int) -> bool:
    now = time.time()
    buckets[:] = [t for t in buckets if now - t < window_seconds]
    if len(buckets) >= max_requests:
        return False
    buckets.append(now)
    return True

async def require_api_key(request: Request, authorization: str | None = Header(None)) -> str:
    try:
        key = verify_api_key(authorization, settings.api_keys)
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not _is_allowed(ip_requests[request.client.host], 60, 10):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    if not _is_allowed(global_requests, 60, 100):
        raise HTTPException(status_code=429, detail="Global rate limit exceeded")

    return key
