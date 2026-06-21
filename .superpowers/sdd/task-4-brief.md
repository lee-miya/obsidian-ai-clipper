# Task 4 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 4: SQLite Job Storage

**Files:**
- Create: `src/core/storage.py`
- Test: `tests/test_storage.py`

**Interfaces:**
- Produces: `JobStore` async class with methods `create_job(url)`, `get_job(job_id)`, `update_status(job_id, status, **fields)`, `list_jobs(status=None, limit=50)`, `list_failed_jobs()`.

- [ ] **Step 1: Write failing test for creating a job**

```python
import pytest
from src.core.storage import JobStore
from src.core.models import JobStatus

@pytest.fixture
async def store(tmp_path):
    db_path = tmp_path / "test.db"
    s = JobStore(str(db_path))
    await s.init()
    return s

async def test_create_job(store):
    job = await store.create_job("https://example.com")
    assert job["url"] == "https://example.com"
    assert job["status"] == JobStatus.PENDING.value
```

- [ ] **Step 2: Implement `src/core/storage.py`**

```python
import aiosqlite
from datetime import datetime, timezone
from src.core.models import JobStatus

class JobStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    stage TEXT,
                    last_error TEXT,
                    raw_html_path TEXT,
                    extracted_json_path TEXT,
                    vault_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)
            """)
            await db.commit()

    async def create_job(self, url: str) -> dict:
        import uuid
        now = datetime.now(timezone.utc).isoformat()
        job_id = f"clip_{uuid.uuid4().hex[:12]}"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO jobs (id, url, status, max_retries, stage, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (job_id, url, JobStatus.PENDING.value, 3, "pending", now, now),
            )
            await db.commit()
        return await self.get_job(job_id)

    async def get_job(self, job_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_status(self, job_id: str, status: JobStatus, **fields) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        fields["status"] = status.value
        fields["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [job_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE jobs SET {set_clause} WHERE id = ?", values)
            await db.commit()
        return await self.get_job(job_id)

    async def list_jobs(self, status: JobStatus | None = None, limit: int = 50) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                async with db.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit),
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with db.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
                ) as cursor:
                    rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def list_failed_jobs(self) -> list[dict]:
        return await self.list_jobs(status=JobStatus.FAILED)
```

- [ ] **Step 3: Run storage tests**

Run: `pytest tests/test_storage.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/core/storage.py tests/test_storage.py
git commit -m "feat: add SQLite job storage"
```

---

