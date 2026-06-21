def verify_api_key(header: str | None, allowed_keys: list[str]) -> str:
    if not header or not header.startswith("Bearer "):
        raise ValueError("Invalid authorization header")
    key = header[7:]
    if key not in allowed_keys:
        raise ValueError("Invalid API key")
    return key
