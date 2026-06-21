Task 7 fix instructions:

1. Update `src/ai/kimi_client.py`:
   - Remove `response_format` from payload (Moonshot API does not support it)
   - Change default model from `"kimi2.6"` to `"kimi-k2.6"`
   - Add explicit `Content-Type: application/json` header
   - Add JSON parsing fallback: wrap `json.loads(raw)` in try/except; on failure try to extract JSON from markdown fences; if still failing, raise a clear exception or return a fallback dict (but per design spec, fallback should happen in worker, not client — so raise a custom `KimiAPIError` or `json.JSONDecodeError`)
   - Add retry logic with exponential backoff for `httpx.HTTPStatusError` and `httpx.RequestError`, up to 3 retries

2. Update `tests/test_ai_client.py`:
   - Update model name in test
   - Add test for HTTP error retry
   - Add test for malformed JSON response

3. Update `.env.example` and `src/config.py` default if needed: `KIMI_MODEL` default should be `"kimi-k2.6"`

4. Update `prompts/clip.md` if needed (already instructs to return valid JSON, keep as is)

5. Run tests with `uv run pytest tests/test_ai_client.py -v`

6. Commit with message: `fix: correct Kimi API payload, model name, add retry and error handling`

Append fix details to `.superpowers/sdd/task-7-report.md`.
