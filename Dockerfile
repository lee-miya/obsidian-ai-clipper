FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -e ".[dev]"

# Install Playwright browsers (requires root for system deps)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY src ./src
COPY prompts ./prompts

# Create non-root user
RUN groupadd -r clipper && useradd -r -g clipper clipper
RUN mkdir -p /data && chown clipper:clipper /data

# Persist Playwright browsers for the runtime user
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

USER clipper

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
