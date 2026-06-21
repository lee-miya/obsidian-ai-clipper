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

## HTTPS Deployment

### Option 1: Traefik with Let's Encrypt (recommended for production)

The included `docker-compose.yml` bundles Traefik as a reverse proxy with automatic TLS via Let's Encrypt.

1. Edit `docker-compose.yml` and replace the placeholder values:
   - `your-email@example.com` — the email Let's Encrypt will use for expiry notices
   - `clipper.example.com` — your actual domain name

2. Ensure port 443 is reachable from the internet (Let's Encrypt HTTP challenge requires inbound HTTPS or TLS-ALPN).

3. Start the stack:
   ```bash
   docker compose up -d
   ```

Traefik will automatically obtain and renew certificates for your domain.

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

Alternatively, use a reverse proxy (nginx, Traefik, Caddy) in front of Uvicorn — this is the recommended approach since Uvicorn does not directly support p12 files.

## Development

Create and sync the Python environment with uv:

```bash
uv sync
```

Run commands inside the managed environment:

```bash
uv run pytest
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
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
