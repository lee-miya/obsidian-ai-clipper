# Task 4 Report: SQLite Job Storage

**Status:** DONE

## Files Created
- `src/core/storage.py` — JobStore class with SQLite backend
- `tests/test_storage.py` — Test suite for storage operations

## Implementation Summary
Created `JobStore` async class with methods:
- `init()` — Initializes SQLite DB with jobs table and status index
- `create_job(url)` — Creates a new job with PENDING status
- `get_job(job_id)` — Retrieves job by ID
- `update_status(job_id, status, **fields)` — Updates job status and fields
- `list_jobs(status=None, limit=50)` — Lists jobs, optionally filtered by status
- `list_failed_jobs()` — Convenience method to list failed jobs

## Commands Run
```
uv run pytest tests/test_storage.py -v
```
Result: 6 passed in 0.71s

## Notes
- Set `KIMI_API_KEY` env var in test fixture to satisfy Settings requirement
- All tests pass successfully
- Committed as `ebbc107`
