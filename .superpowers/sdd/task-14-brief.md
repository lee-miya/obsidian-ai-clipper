# Task 14 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 14: HTTPS / TLS Configuration

**Files:**
- Modify: `docker-compose.yml`
- Create: `nginx.conf` (optional)
- Create: `scripts/init-letsencrypt.sh` (optional)

**Interfaces:**
- Produces: production HTTPS deployment configuration.

- [ ] **Step 1: Add Traefik to `docker-compose.yml` for Let's Encrypt**

```yaml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"

  clipper:
    build: .
    container_name: obsidian-ai-clipper
    expose:
      - "8000"
    env_file:
      - .env
    volumes:
      - ${VAULT_PATH}:/data/vault
      - ./data:/data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.clipper.rule=Host(`clipper.example.com`)"
      - "traefik.http.routers.clipper.tls=true"
      - "traefik.http.routers.clipper.tls.certresolver=letsencrypt"
    restart: unless-stopped
```

- [ ] **Step 2: Add p12 certificate support instructions to `README.md`**

Explain how to mount a p12 file and configure Uvicorn with it:

```bash
# If using a p12 certificate directly, start uvicorn with:
uvicorn src.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile ... --ssl-certfile ...
```

Note: Uvicorn does not directly support p12; use OpenSSL to convert p12 to PEM key/cert or use a reverse proxy.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml README.md
git commit -m "docs: add HTTPS deployment guidance"
```

---

