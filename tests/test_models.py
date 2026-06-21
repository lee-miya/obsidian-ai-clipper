from src.core.models import ClipRequest, JobStatus

def test_clip_request_valid_url():
    req = ClipRequest(url="https://example.com/article")
    assert str(req.url) == "https://example.com/article"

def test_job_status_values():
    assert JobStatus.PENDING.value == "pending"
