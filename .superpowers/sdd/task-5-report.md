# Task 5 Report: Static and Dynamic Fetchers

## Status: DONE

## Files Created
- `src/fetcher/static_fetcher.py` - HTTP client-based static fetcher using httpx
- `src/fetcher/dynamic_fetcher.py` - Playwright-based dynamic fetcher for JavaScript-rendered pages
- `src/fetcher/fetcher.py` - Unified fetcher that tries static first, falls back to dynamic
- `tests/test_fetcher.py` - Test for static fetcher using respx mock

## Commands Run
- `uv run pytest tests/test_fetcher.py -v` - Result: 1 passed
- `uv run playwright install chromium` - Playwright browser installation initiated (backgrounded)
- `git add src/fetcher/ tests/test_fetcher.py`
- `git commit -m "feat: add static and dynamic fetchers"` - Committed as a63f73a

---

## Fix Status: DONE

### Fixes Applied (per task-5-fix.md)
1. **Removed committed `__pycache__`**: `src/fetcher/__pycache__/` deleted from git and `.gitignore` created with standard Python ignores
2. **Narrowed exception handling**: `src/fetcher/fetcher.py` now catches only `httpx.HTTPStatusError`, `httpx.RequestError`, `httpx.TimeoutException` instead of bare `Exception`
3. **Resource cleanup with context managers**: `src/fetcher/dynamic_fetcher.py` now uses nested `async with` for browser and context lifecycle
4. **Expanded test coverage**: `tests/test_fetcher.py` added:
   - `test_fetch_html_fallback_to_dynamic` — verifies static failure falls back to dynamic fetcher
   - `test_dynamic_fetcher_returns_html` — verifies dynamic fetcher returns HTML (mocked)

### Commands Run
- `git rm -r src/fetcher/__pycache__` — removed pycache from git
- `uv run pytest tests/test_fetcher.py -v` — Result: **3 passed** (up from 1)
- `git add .gitignore src/fetcher/fetcher.py src/fetcher/dynamic_fetcher.py tests/test_fetcher.py`
- `git commit -m "fix: address Task 5 review feedback (pycache, exception handling, resource cleanup)"` — Committed as e50c530

### Files Changed
- `.gitignore` (created)
- `src/fetcher/__pycache__/static_fetcher.cpython-314.pyc` (deleted)
- `src/fetcher/fetcher.py` (narrowed exception handling)
- `src/fetcher/dynamic_fetcher.py` (context managers for resource cleanup)
- `tests/test_fetcher.py` (added fallback and dynamic fetcher tests)

### Concerns
None. All fixes applied and tests pass.
