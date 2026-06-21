# Task 12 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 12: Rate Limiting and Security Headers

**Files:**
- Modify: `src/api/deps.py`
- Modify: `src/main.py`
- Test: `tests/test_rate_limit.py`

**Interfaces:**
- Produces: rate limit dependency applied to `/api/clip`.

- [ ] **Step 1: Add simple in-memory rate limiter**

Modify `src/api/deps.py`:

```python
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
```

- [ ] **Step 2: Add security headers middleware in `src/main.py`**

```python
from fastapi import FastAPI, Request
from fastapi.responses import Response
from src.api.routes import router as api_router
from src.web.routes import router as web_router

app = FastAPI(title="Obsidian AI Clipper")
app.include_router(api_router)
app.include_router(web_router)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3: Add rate limit test**

```python
from fastapi.testclient import TestClient
from src.main import app

def test_rate_limit_after_many_requests():
    client = TestClient(app)
    for i in range(10):
        response = client.post("/api/clip", json={"url": "https://example.com"}, headers={"Authorization": "Bearer test-key"})
    response = client.post("/api/clip", json={"url": "https://example.com"}, headers={"Authorization": "Bearer test-key"})
    assert response.status_code == 429
```

Note: This test assumes `API_KEYS` env includes `test-key`. Set via test fixture or conftest.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_rate_limit.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/deps.py src/main.py tests/test_rate_limit.py
git commit -m "feat: add rate limiting and security headers"
```

---

