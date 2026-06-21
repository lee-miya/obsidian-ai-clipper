from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

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
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    client_version: str = "1.0.0"

class ClipResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str = "已接收，正在后台处理"

class JobResponse(BaseModel):
    model_config = ConfigDict(extra='allow')

    job_id: str | None = None
    id: str | None = None
    status: JobStatus | None = None
    stage: str | None = None
    retry_count: int = 0
    vault_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
