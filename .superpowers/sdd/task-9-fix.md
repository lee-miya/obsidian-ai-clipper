Task 9 fix instructions:

1. Fix exception handling in `src/worker/worker.py`:
   - In the AI retry loop, re-raise `asyncio.CancelledError` before catching generic `Exception`
   - In the outer `except Exception` block, also re-raise `asyncio.CancelledError`

2. Record AI failure in fallback case:
   - When all retries are exhausted, update job status to `NEEDS_REVIEW` with `last_error` containing the last error, and return (do not save as done)
   - Alternatively, save the fallback content but mark status as `NEEDS_REVIEW` — per design spec "AI 处理最终失败时，仍保存原始提取内容到 Vault，并标记 ai_failed"
   - Better approach: save fallback content, set `status="needs_review"` and record `last_error`

3. Add tests for:
   - Content too short → status `needs_review`
   - Fetch failure → status `failed` or `pending` with retry_count incremented
   - AI retry exhaustion → fallback saved, status `needs_review`
   - `CancelledError` propagation (optional but good)

4. Consider whether `Settings()` defaults weakening is acceptable. The reviewer noted it helps testability. Keep as is for now, but we may want to validate `kimi_api_key` is non-empty in worker before calling Kimi.

5. Run tests: `uv run pytest tests/test_worker.py -v`

6. Commit with message: `fix: improve worker exception handling and AI fallback tracking`

Append fix details to `.superpowers/sdd/task-9-report.md`.
