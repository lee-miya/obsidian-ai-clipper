## Task 10 Report: FastAPI API Routes

**Status: DONE**

### Files created/modified
- `src/api/__init__.py` — created (empty package init)
- `src/api/deps.py` — created (require_api_key dependency)
- `src/api/routes.py` — created (POST /api/clip, GET /api/jobs/{job_id})
- `src/main.py` — modified (added api_router, updated health endpoint)
- `tests/test_api.py` — created (10 tests across 5 test classes)

### Commands run and results
1. `uv run pytest tests/test_api.py -v` — 10 passed, 2 deprecation warnings (on_event, Starlette httpx)
2. `uv run pytest tests/ -v` — 45 passed, 0 failures, no regressions

### Concerns
- The `on_event("startup")` decorator in routes.py triggers a deprecation warning. FastAPI recommends lifespan event handlers. This is cosmetic and the functionality works correctly.
- The Starlette TestClient deprecation warning about httpx vs httpx2 is a library-level warning, not actionable in our code.
- The brief's tests reference `pytest` fixture directly; the implementation uses `pytest_asyncio` for the async client fixture to properly initialize the database store before tests.
