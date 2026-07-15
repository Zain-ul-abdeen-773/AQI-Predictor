# ─────────────────────────────────────────────────────────────────────────────
# Multi-Stage Dockerfile — Pearls AQI Predictor
# Optimized for < 500MB final image size
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Security: run as non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY config/ ./config/
COPY data_pipeline/ ./data_pipeline/
COPY feature_pipeline/ ./feature_pipeline/
COPY training_pipeline/ ./training_pipeline/
COPY deployment/ ./deployment/
COPY infrastructure/ ./infrastructure/

# Create data directories
RUN mkdir -p /app/data /app/models /app/logs \
    && chown -R appuser:appuser /app

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; r = requests.get('http://localhost:8000/health'); exit(0 if r.ok else 1)" || exit 1

# Switch to non-root user
USER appuser

# Expose API port
EXPOSE 8000

# Default command: Run FastAPI with Uvicorn
CMD ["uvicorn", "deployment.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--log-level", "info"]
