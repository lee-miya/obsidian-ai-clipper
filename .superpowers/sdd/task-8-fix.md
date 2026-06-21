Task 8 fix instructions:

1. Fix `src/writer/__init__.py` — it currently duplicates the entire vault_writer implementation. Replace it with:
```python
from src.writer.vault_writer import save_clip

__all__ = ["save_clip"]
```

2. Fix YAML frontmatter escaping in `src/writer/vault_writer.py`:
   - Import `yaml` (PyYAML is available as a transitive dependency via dateparser or add `pyyaml` to dependencies if needed — it is already in uv.lock as pyyaml==6.0.3 so it should be installable)
   - Generate frontmatter as a Python dict, then dump with `yaml.safe_dump` wrapped with `---\n` and `\n---\n`
   - This avoids manual escaping issues with quotes and newlines

3. Fix `download_image` to log exceptions:
   - Add `import logging` and use `logger = logging.getLogger(__name__)`
   - In the `except Exception:` block, log a warning with the image URL and exception
   - Keep the fallback to original URL behavior

4. Clean up `download_image` filename construction:
   - Change signature to `async def download_image(url: str, clip_dir: Path, idx: int) -> str`
   - Use filename like `f"image_{idx}.{ext}"`
   - Update the call site in `save_clip`

5. Expand tests in `tests/test_vault_writer.py`:
   - Test directory structure: `Clips/人工智能/2026-.../index.md`
   - Test frontmatter YAML parses correctly
   - Test image download with mocked httpx (use `respx_mock` or monkeypatch httpx.AsyncClient)
   - Test collision handling when saving two clips with same title
   - Test fallback when ai_result is empty/missing fields

6. Run tests: `uv run pytest tests/test_vault_writer.py -v`

7. Commit with message: `fix: dedupe vault writer, use YAML frontmatter, improve tests`

Append fix details to `.superpowers/sdd/task-8-report.md`.
