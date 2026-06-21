# Obsidian AI Clipper

Personal AI-powered web clipper for Obsidian Vaults. Save web pages as structured Markdown using Kimi AI.

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

## Deployment to Rocky Linux 9.5

Run the automated deployment script:

```bash
sudo bash scripts/deploy.sh
```

The script will:
1. Install Docker and dependencies
2. Prompt for API keys and configuration
3. Optionally configure Let's Encrypt HTTPS
4. Build and start the container

## HTTPS Deployment

### Option 1: Traefik with Let's Encrypt (recommended for production)

The included `docker-compose.yml` can bundle Traefik as a reverse proxy with automatic TLS via Let's Encrypt.

1. Run `bash scripts/deploy.sh` and provide your domain and email when prompted.

2. Ensure port 443 is reachable from the internet.

3. Traefik will automatically obtain and renew certificates for your domain.

### Option 2: p12 / PFX certificate

If you already have a `.p12` (PKCS#12) certificate, convert it to PEM format that Uvicorn can use:

```bash
# Extract the private key
openssl pkcs12 -in cert.p12 -nocerts -nodes -out key.pem

# Extract the certificate
openssl pkcs12 -in cert.p12 -clcerts -nokeys -out cert.pem
```

Then start Uvicorn with the PEM files:

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 \
  --ssl-keyfile key.pem --ssl-certfile cert.pem
```

Alternatively, use a reverse proxy (nginx, Traefik, Caddy) in front of Uvicorn — this is the recommended approach.

## Development

Create and sync the Python environment with uv:

```bash
uv sync --group dev
```

Install Playwright browsers (required for dynamic page fetching):

```bash
uv run playwright install chromium
```

Run commands inside the managed environment:

```bash
uv run pytest
uv run pytest tests/test_worker.py -v
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEYS` | Comma-separated list of valid API keys | (required) |
| `KIMI_API_KEY` | Kimi Code API key from kimi.com/code/console | (required) |
| `KIMI_BASE_URL` | Kimi Code API endpoint | `https://api.kimi.com/coding/v1` |
| `KIMI_MODEL` | Model identifier | `kimi-for-coding` |
| `VAULT_PATH` | Path to Obsidian vault | `/data/vault` |
| `DATABASE_PATH` | SQLite database path | `/data/clipper.db` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `RATE_LIMIT_IP` | Per-IP rate limit | `10/minute` |
| `RATE_LIMIT_GLOBAL` | Global rate limit | `100/minute` |
| `MAX_RETRY` | Max retries for failed operations | `3` |

## Architecture

See `CLAUDE.md` for detailed architecture and development conventions.
