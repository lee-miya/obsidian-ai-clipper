from fastapi import Header, HTTPException
from src.config import Settings
from src.core.security import verify_api_key

settings = Settings()


async def require_api_key(authorization: str | None = Header(None)) -> str:
    try:
        return verify_api_key(authorization, settings.api_keys)
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized")
