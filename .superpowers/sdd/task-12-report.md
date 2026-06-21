# Task 12 Report: Rate Limiting and Security Headers

## Status: DONE

## Files Modified

- `src/api/deps.py` — Added in-memory rate limiter with IP-level (10 req/60s) and global (100 req/60s) limits. The `require_api_key` dependency now accepts `request: Request` and applies rate limiting after authentication.
- `src/main.py` — Added security headers middleware (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy: default-src 'self'`).

## Files Created

- `tests/test_rate_limit.py` — 4 tests: IP rate limit triggers at 11th request, global rate limit triggers at 101st request, security headers present on responses, unauthorized requests don't count toward limits.

## Commands Run

- `pytest tests/test_rate_limit.py -v` — 4 passed
- `pytest tests/test_api.py tests/test_web.py -v` — 15 passed (no regressions)

## Concerns

- The rate limiter is in-memory only, so limits reset on process restart and are not shared across workers. Acceptable for current scope; a Redis-backed limiter could be added later.
- The `test_global_rate_limit` test implicitly includes the IP check (10 requests per IP per window), so hitting 100 global requests requires the IP counter to also be cleared — this is done in the fixture `rate_limit_client` which clears both buckets before each test.
