import json
import httpx
from src.extractor.extractor import ExtractedContent

class KimiClient:
    def __init__(self, api_key: str, model: str = "kimi2.6"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.moonshot.cn/v1"

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
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"]
            return json.loads(raw)
