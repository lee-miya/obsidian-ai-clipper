# Obsidian AI Clipper

Personal AI-powered web clipper for Obsidian Vaults.

## Quick Start

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your API keys and vault path.

3. Build and run with Docker Compose:
   ```bash
   docker compose up --build
   ```

4. The API will be available at `http://localhost:8000`.

## Development

Install locally in editable mode:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEYS` | Comma-separated list of valid API keys | (required) |
| `KIMI_API_KEY` | Kimi API key for AI features | (required) |
| `KIMI_MODEL` | Model identifier | `kimi2.6` |
| `VAULT_PATH` | Path to Obsidian vault | `/data/vault` |
| `DATABASE_PATH` | SQLite database path | `/data/clipper.db` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `RATE_LIMIT_IP` | Per-IP rate limit | `10/minute` |
| `RATE_LIMIT_GLOBAL` | Global rate limit | `100/minute` |
| `MAX_RETRY` | Max retries for failed operations | `3` |
