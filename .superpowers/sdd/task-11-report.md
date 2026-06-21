# Task 11 Report

**Status:** DONE

## Summary
Implemented web UI routes and templates for browsing clips in the Obsidian AI Clipper.

## Files Created
- `src/web/__init__.py` — package init (empty)
- `src/web/routes.py` — web router with 4 endpoints (/web, /web/clips/{id}, /web/failed, /web/queue)
- `src/web/templates/base.html` — base layout with navigation and styling
- `src/web/templates/list.html` — clip list table
- `src/web/templates/detail.html` — clip detail table
- `src/web/templates/failed.html` — failed jobs table
- `src/web/templates/queue.html` — queue status table (pending/fetching counts)
- `tests/test_web.py` — 5 tests covering all web endpoints

## Files Modified
- `src/main.py` — added `web_router` import and `app.include_router(web_router)`

## Commands Run
1. `uv run pytest tests/test_web.py -v` — 5 passed
2. `uv run pytest tests/test_web.py tests/test_api.py -v` — 15 passed (full suite)

## Design Decisions / Deviations from Brief
1. **TemplateResponse calling convention**: The brief's code passed `{"request": request, "jobs": jobs}` directly to `TemplateResponse`, but Jinja2 3.1.6 has an LRU cache issue where `request` objects (containing dicts) break the template cache key. Changed to use `templates.TemplateResponse(request=request, name="...", context={...})` which separates the name from context and avoids the cache key issue.
2. **Test monkeypatching**: The brief's minimal test would fail because `router.on_event("startup")` does not fire with `TestClient`. Followed the existing pattern from `tests/test_api.py` — use a `client` fixture that monkeypatches settings and store after initializing the database.

## Concerns
- The `on_event("startup")` deprecation warnings will eventually need migration to lifespan handlers across both API and web routers.
- The `Event loop is closed` warning from aiosqlite is pre-existing and not related to this task.
