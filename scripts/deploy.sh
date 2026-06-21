#!/usr/bin/env bash
# Obsidian AI Clipper - Deployment Script for Rocky Linux 9.5
# Run as root or with sudo: ./scripts/deploy.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "============================================"
echo " Obsidian AI Clipper - Rocky Linux 9.5 Deploy"
echo "============================================"
echo ""

# ---- Check OS ----
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "[*] Detected OS: $NAME $VERSION"
fi

# ---- Prompt for sensitive values ----
echo ""
echo "--- Configuration ---"
read -rp "API Key for Chrome extension (comma-separated, e.g. key1,key2): " API_KEYS_INPUT
read -rp "Kimi Code API Key: " KIMI_API_KEY_INPUT
read -rp "Kimi Base URL [https://api.kimi.com/coding/v1]: " KIMI_BASE_URL_INPUT
read -rp "Kimi Model [kimi-for-coding]: " KIMI_MODEL_INPUT
read -rp "Vault path on host [$(pwd)/vault]: " VAULT_PATH_INPUT
read -rp "Database path on host [$(pwd)/data/clipper.db]: " DATABASE_PATH_INPUT
read -rp "Domain for HTTPS (leave blank to skip Let's Encrypt): " DOMAIN_INPUT
read -rp "Email for Let's Encrypt (leave blank to skip): " EMAIL_INPUT

API_KEYS="${API_KEYS_INPUT:-change-me}"
KIMI_API_KEY="${KIMI_API_KEY_INPUT:-sk-xxx}"
KIMI_BASE_URL="${KIMI_BASE_URL_INPUT:-https://api.kimi.com/coding/v1}"
KIMI_MODEL="${KIMI_MODEL_INPUT:-kimi-for-coding}"
VAULT_PATH="${VAULT_PATH_INPUT:-$(pwd)/vault}"
DATABASE_PATH="${DATABASE_PATH_INPUT:-$(pwd)/data/clipper.db}"

# ---- Install system dependencies ----
echo ""
echo "[1/6] Installing system dependencies..."
dnf install -y dnf-plugins-core

# Docker
if ! command -v docker &> /dev/null; then
    echo "  Installing Docker..."
    dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
    dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker
fi

echo "  Docker: $(docker --version)"

# ---- Create directories ----
echo ""
echo "[2/6] Creating directories..."
mkdir -p "$(dirname "$DATABASE_PATH")"
mkdir -p "$VAULT_PATH"

# ---- Write .env ----
echo ""
echo "[3/6] Writing .env..."
cat > .env << EOF
API_KEYS=${API_KEYS}
KIMI_API_KEY=${KIMI_API_KEY}
KIMI_BASE_URL=${KIMI_BASE_URL}
KIMI_MODEL=${KIMI_MODEL}
VAULT_PATH=/data/vault
DATABASE_PATH=/data/clipper.db
LOG_LEVEL=INFO
RATE_LIMIT_IP=10/minute
RATE_LIMIT_GLOBAL=100/minute
MAX_RETRY=3
EOF
chmod 600 .env
echo "  .env written (permissions: 600)."

# ---- Docker Compose setup ----
echo ""
echo "[4/6] Configuring Docker Compose..."

if [ -n "$DOMAIN_INPUT" ] && [ -n "$EMAIL_INPUT" ]; then
    echo "  HTTPS enabled via Traefik + Let's Encrypt for domain: $DOMAIN_INPUT"
    cat > docker-compose.yml << COMPOSE_EOF
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=${EMAIL_INPUT}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
    restart: unless-stopped

  clipper:
    build: .
    container_name: obsidian-ai-clipper
    expose:
      - "8000"
    env_file:
      - .env
    volumes:
      - ${VAULT_PATH}:/data/vault
      - $(dirname "$DATABASE_PATH"):/data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.clipper.rule=Host(\`${DOMAIN_INPUT}\`)"
      - "traefik.http.routers.clipper.tls=true"
      - "traefik.http.routers.clipper.tls.certresolver=letsencrypt"
    restart: unless-stopped
COMPOSE_EOF
else
    echo "  HTTPS not configured — running on port 8000 only."
    cat > docker-compose.yml << COMPOSE_EOF
services:
  clipper:
    build: .
    container_name: obsidian-ai-clipper
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ${VAULT_PATH}:/data/vault
      - $(dirname "$DATABASE_PATH"):/data
    restart: unless-stopped
COMPOSE_EOF
fi

# ---- Firewall ----
echo ""
echo "[5/6] Configuring firewall..."
if command -v firewall-cmd &> /dev/null && systemctl is-active --quiet firewalld 2>/dev/null; then
    if [ -n "$DOMAIN_INPUT" ]; then
        firewall-cmd --permanent --add-service=https 2>/dev/null || true
    else
        firewall-cmd --permanent --add-port=8000/tcp 2>/dev/null || true
    fi
    firewall-cmd --reload 2>/dev/null || true
    echo "  Firewall configured."
else
    echo "  firewalld not active — skipping firewall configuration."
fi

# ---- Build & Start ----
echo ""
echo "[6/6] Building and starting containers..."
docker compose build --pull
docker compose up -d

echo ""
echo "============================================"
echo " Deploy complete!"
echo "============================================"
echo ""
if [ -n "$DOMAIN_INPUT" ]; then
    echo " Web UI:  https://${DOMAIN_INPUT}/web"
    echo " API:     https://${DOMAIN_INPUT}/api"
else
    echo " API:     http://$(hostname -I | awk '{print $1}'):8000/api"
    echo " Web UI:  http://$(hostname -I | awk '{print $1}'):8000/web"
fi
echo ""
echo " Check status:  docker compose ps"
echo " View logs:     docker compose logs -f"
echo " Health check:  curl http://localhost:8000/health"
