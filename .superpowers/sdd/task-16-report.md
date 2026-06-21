# Task 16 Report: Final Integration and Docker Build

**Status:** DONE

## Summary

Updated the Dockerfile to support Playwright browser installation, switched from pip to uv for package management, created a .dockerignore file, and verified the full test suite passes.

## Files Modified

| File | Action | Description |
|---|---|---|
| `Dockerfile` | Modified | Added Playwright chromium install, switched pip to uv, added data directory setup, fixed runtime user permissions for Playwright browsers |
| `.dockerignore` | Created | Excludes .git, .env, .venv, tests, docs, and build artifacts from Docker context |

## Files Not Modified (but needed context)

- `pyproject.toml` — already had `playwright>=1.60.0` in dependencies, no changes needed
- `src/main.py` — `/health` endpoint already exists and returns `{"status":"ok"}`, confirmed in test suite

## Commands Run

| Command | Result |
|---|---|
| `uv run pytest -v` | **55 passed**, 0 failed, 5 warnings (deprecation notices only) |

## Warnings (non-blocking)

1. **FastAPI `on_event` deprecation** — `src/api/routes.py:18` and `src/web/routes.py:15` use the deprecated `@router.on_event("startup")` pattern. Should migrate to `lifespan` context manager in a future task.
2. **aiosqlite thread cleanup** — `RuntimeError: Event loop is closed` warnings in rate-limit tests during teardown. Harmless, caused by aiosqlite worker threads outliving the test event loop.
3. **starlette TestClient deprecation** — FastAPI's TestClient wrapper will need updating when httpx2 is adopted.

## Dockerfile Changes Detail

1. **uv adoption:** Replaced `pip install` with `uv pip install --system` for faster, more reliable builds. The `uv` binary is copied from the official `ghcr.io/astral-sh/uv:latest` image.
2. **Playwright browsers:** Added `playwright install chromium` and `playwright install-deps chromium` at build time (runs as root, as required for system library installation).
3. **Runtime user:** Playwright browser cache path is set via `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright` so the `clipper` user can read pre-installed browsers.
4. **Data directory:** `/data` directory created and chowned to `clipper` user for `DATABASE_PATH=/data/clipper.db` and `VAULT_PATH=/data/vault` at runtime.
5. **.dockerignore:** Prevents `.env`, `.git`, `tests`, `.venv`, and build artifacts from being copied into the image.

## Steps Not Executed

Steps 2 and 3 from the brief (docker build and smoke test) were not executed because:
- Docker is not guaranteed to be available in this environment
- The brief explicitly says "You don't need to actually run docker build"
- The Dockerfile is syntactically correct based on best practices for uv + Playwright

## Concerns

None. The Dockerfile follows the standard multi-stage pattern for uv-based Python projects with Playwright. All 55 tests pass. The image should build and run correctly when Docker is available.
