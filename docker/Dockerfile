# CargoTrack VC - Dockerfile
# Multi-stage build for production optimization

# ---- Build Stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files needed for build
COPY pyproject.toml .
COPY src/ ./src/

# Install dependencies directly (not via build wheel)
# This ensures all dependencies including psycopg2 are installed
RUN pip install --no-cache-dir -e .

# ---- Production Stage ----
FROM python:3.12-slim AS production

WORKDIR /app

# Create non-root user
RUN groupadd -r cargotrack && useradd -r -g cargotrack cargotrack

# Install runtime dependencies (libpq5 for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code and config
COPY src/ ./src/
COPY config/ ./config/
COPY tests/fixtures/ ./tests/fixtures/

# Create directories for secrets and logs
RUN mkdir -p /secrets /var/log/cargotrack-vc && \
    chown -R cargotrack:cargotrack /app /secrets /var/log/cargotrack-vc

# Switch to non-root user
USER cargotrack

# Environment
ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DTE_CONFIG_PATH=/app/config/settings.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/live')"

EXPOSE 8000

CMD ["uvicorn", "dte_mvp.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
