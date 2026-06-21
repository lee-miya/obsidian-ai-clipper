import re
import logging
import yaml
import httpx
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from src.extractor.extractor import ExtractedContent

logger = logging.getLogger(__name__)

SLUG_MAX = 60


def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w一-龥-]+", "-", name).strip("-")
    return name[:SLUG_MAX]


async def download_image(url: str, clip_dir: Path, idx: int) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        ext = response.headers.get("content-type", "").split("/")[-1]
        if not ext or ext not in {"png", "jpg", "jpeg", "gif", "webp", "svg"}:
            ext = "png"
        filename = f"image_{idx}.{ext}"
        image_path = clip_dir / filename
        image_path.write_bytes(response.content)
        return filename


async def save_clip(
    job_id: str,
    url: str,
    ai_result: dict,
    extracted: ExtractedContent,
    vault_root: str,
) -> Path:
    category = safe_filename(ai_result.get("category") or "未分类")
    title = ai_result.get("title") or extracted.title or "untitled"
    date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = safe_filename(title) or "clip"
    dir_name = f"{date_prefix}-{slug}"
    clip_dir = Path(vault_root) / "Clips" / category / dir_name
    clip_dir.mkdir(parents=True, exist_ok=True)

    index_path = clip_dir / "index.md"
    counter = 1
    while index_path.exists():
        clip_dir = Path(vault_root) / "Clips" / category / f"{dir_name}-{counter}"
        clip_dir.mkdir(parents=True, exist_ok=True)
        index_path = clip_dir / "index.md"
        counter += 1

    md_content = ai_result.get("content_markdown") or extracted.content
    image_map = {}
    for idx, img in enumerate(extracted.images):
        try:
            filename = await download_image(img["src"], clip_dir, idx)
            image_map[img["src"]] = filename
        except Exception as e:
            logger.warning("Failed to download image %s: %s", img["src"], e)
            image_map[img["src"]] = img["src"]

    for original, replacement in image_map.items():
        md_content = md_content.replace(original, replacement)

    frontmatter_dict = {
        "title": title,
        "source_url": url,
        "domain": urlparse(url).netloc,
        "category": category,
        "tags": ai_result.get("tags", []),
        "summary": ai_result.get("summary", ""),
        "author": ai_result.get("author", ""),
        "published_at": ai_result.get("published_at", ""),
        "clipped_at": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        "status": "done",
    }
    frontmatter = "---\n" + yaml.safe_dump(frontmatter_dict, allow_unicode=True, sort_keys=False) + "---\n\n"

    temp_path = clip_dir / ".index.md.tmp"
    temp_path.write_text(frontmatter + md_content, encoding="utf-8")
    temp_path.replace(index_path)
    return index_path
