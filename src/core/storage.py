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
