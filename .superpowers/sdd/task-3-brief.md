# Task 3 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 3: URL Validation and Security Helpers

**Files:**
- Create: `src/utils/url.py`
- Create: `src/core/security.py`
- Test: `tests/test_url.py`
- Test: `tests/test_security.py`

**Interfaces:**
- Produces: `validate_public_url(url: str) -> str`, `is_private_ip(host: str) -> bool`, `verify_api_key(header: str | None, allowed: list[str]) -> str`.

- [ ] **Step 1: Write failing tests for URL validation**

```python
import pytest
from src.utils.url import validate_public_url

def test_valid_https_url():
    assert validate_public_url("https://example.com") == "https://example.com"

def test_rejects_localhost():
    with pytest.raises(ValueError):
        validate_public_url("http://localhost:8000")

def test_rejects_private_ip():
    with pytest.raises(ValueError):
        validate_public_url("http://192.168.1.1")

def test_rejects_non_http_protocol():
    with pytest.raises(ValueError):
        validate_public_url("ftp://example.com")
```

- [ ] **Step 2: Implement `src/utils/url.py`**

```python
import ipaddress
from urllib.parse import urlparse

PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def is_private_ip(host: str) -> bool:
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in net for net in PRIVATE_NETWORKS)
    except ValueError:
        return False

def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https URLs are allowed")
    if not parsed.hostname:
        raise ValueError("Invalid URL")
    host = parsed.hostname.lower()
    if host in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Localhost URLs are not allowed")
    if is_private_ip(host):
        raise ValueError("Private IP addresses are not allowed")
    return url
```

- [ ] **Step 3: Run URL tests**

Run: `pytest tests/test_url.py -v`  
Expected: PASS

- [ ] **Step 4: Write failing tests for API key verification**

```python
import pytest
from src.core.security import verify_api_key

def test_valid_key():
    assert verify_api_key("Bearer valid-key", ["valid-key"]) == "valid-key"

def test_missing_header():
    with pytest.raises(ValueError):
        verify_api_key(None, ["valid-key"])

def test_invalid_key():
    with pytest.raises(ValueError):
        verify_api_key("Bearer wrong-key", ["valid-key"])
```

- [ ] **Step 5: Implement `src/core/security.py`**

```python
def verify_api_key(header: str | None, allowed_keys: list[str]) -> str:
    if not header or not header.startswith("Bearer "):
        raise ValueError("Invalid authorization header")
    key = header[7:]
    if key not in allowed_keys:
        raise ValueError("Invalid API key")
    return key
```

- [ ] **Step 6: Run security tests**

Run: `pytest tests/test_security.py -v`  
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/utils/url.py src/core/security.py tests/test_url.py tests/test_security.py
git commit -m "feat: add URL validation and API key security"
```

---

