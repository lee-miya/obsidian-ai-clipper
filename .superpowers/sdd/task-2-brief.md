# Task 2 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 2: Configuration and Core Models

**Files:**
- Create: `src/config.py`
- Create: `src/core/models.py`
- Create: `src/main.py` (initial)
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `Settings` singleton, Pydantic models `ClipRequest`, `ClipResponse`, `JobResponse`, `JobStatus` enum.

- [ ] **Step 1: Write failing test for config loading**

```python
import os
from src.config import Settings

def test_settings_loads_api_keys():
    os.environ["API_KEYS"] = "key1,key2"
    settings = Settings()
    assert settings.api_keys == ["key1", "key2"]
```

Run: `pytest tests/test_config.py::test_settings_loads_api_keys -v`  
Expected: FAIL (Settings not defined)

- [ ] **Step 2: Implement `src/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_keys: list[str]
    kimi_api_key: str
    kimi_model: str = "kimi2.6"
    vault_path: str = "/data/vault"
    database_path: str = "/data/clipper.db"
    log_level: str = "INFO"
    rate_limit_ip: str = "10/minute"
    rate_limit_global: str = "100/minute"
    max_retry: int = 3
```

- [ ] **Step 3: Run test**

Run: `pytest tests/test_config.py::test_settings_loads_api_keys -v`  
Expected: PASS

- [ ] **Step 4: Write failing test for models**

```python
from src.core.models import ClipRequest, JobStatus

def test_clip_request_valid_url():
    req = ClipRequest(url="https://example.com/article")
    assert str(req.url) == "https://example.com/article"

def test_job_status_values():
    assert JobStatus.PENDING.value == "pending"
```

- [ ] **Step 5: Implement `src/core/models.py`**

```python
from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl

class JobStatus(str, Enum):
    PENDING = "pending"
    FETCHING = "fetching"
    EXTRACTING = "extracting"
    AI_PROCESSING = "ai_processing"
    SAVING = "saving"
    DONE = "done"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"

class ClipRequest(BaseModel):
    url: HttpUrl
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    client_version: str = "1.0.0"

class ClipResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str = "已接收，正在后台处理"

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    stage: str | None = None
    retry_count: int = 0
    vault_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_config.py tests/test_models.py -v`  
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/config.py src/core/models.py src/main.py tests/test_config.py tests/test_models.py
git commit -m "feat: add configuration and core models"
```

---

