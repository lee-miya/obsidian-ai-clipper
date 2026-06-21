import json
import httpx
from src.extractor.extractor import ExtractedContent

class KimiAPIError(Exception):
    pass

class KimiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.kimi.com/coding/v1", model: str = "kimi-for-coding"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def process(self, content: ExtractedContent, url: str) -> dict:
        with open("prompts/clip.md", encoding="utf-8") as f:
            system_prompt = f.read()

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({
                    "url": url,
                    "title": content.title,
                    "domain": url.split("/")[2],
                    "content": content.content,
                    "images": content.images,
                    "code_blocks": content.code_blocks,
                }, ensure_ascii=False)},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            for attempt in range(3):
                try:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    raw = data["choices"][0]["message"]["content"]
                    try:
                        return json.loads(raw)
                    except json.JSONDecodeError:
                        # Try to extract JSON from markdown fences
                        stripped = raw.strip()
                        if stripped.startswith("```"):
                            # Extract content between fences
                            lines = stripped.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].startswith("```"):
                                lines = lines[:-1]
                            stripped = "\n".join(lines).strip()
                            return json.loads(stripped)
                        raise KimiAPIError(f"Invalid JSON response from Kimi API: {raw[:200]}")
                except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                    if attempt == 2:
                        raise KimiAPIError(f"Kimi API request failed after 3 retries: {exc}") from exc
                    await __import__('asyncio').sleep(2 ** attempt)
            return {}
