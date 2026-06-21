# Task 1 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `Dockerfile`
- Create: `README.md`

**Interfaces:**
- Produces: Python package metadata, dependency list, container orchestration files, environment template.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "obsidian-ai-clipper"
version = "0.1.0"
description = "Personal AI-powered web clipper for Obsidian Vaults"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "aiosqlite>=0.20.0",
    "httpx>=0.27.0",
    "trafilatura>=1.9.0",
    "beautifulsoup4>=4.12.0",
    "jinja2>=3.1.4",
    "python-multipart>=0.0.9",
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-httpx>=0.30.0",
    "respx>=0.21.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `.env.example`**

```bash
API_KEYS=change-me-to-a-long-random-string
KIMI_API_KEY=your-kimi-code-api-key
KIMI_MODEL=kimi2.6
VAULT_PATH=/data/vault
DATABASE_PATH=/data/clipper.db
LOG_LEVEL=INFO
RATE_LIMIT_IP=10/minute
RATE_LIMIT_GLOBAL=100/minute
MAX_RETRY=3
```

- [ ] **Step 3: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY src ./src
COPY prompts ./prompts

RUN groupadd -r clipper && useradd -r -g clipper clipper
USER clipper

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Create `docker-compose.yml`**

```yaml
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
      - ./data:/data
    restart: unless-stopped
```

- [ ] **Step 5: Create `README.md`** with build and run instructions.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example Dockerfile docker-compose.yml README.md
git commit -m "chore: project scaffolding"
```

---

