# ─────────────────────────────────────────────────────────────────────────────
# Multi-Stage Dockerfile — Pearls AQI Predictor
# Optimized for < 500MB final image size
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM public.ecr.aws/docker/library/python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies (cmake for pyarrow, librdkafka-dev for confluent-kafka)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    cmake \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM public.ecr.aws/docker/library/python:3.11-slim AS runtime

# Security: run as non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

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

# Default command: Run Flask with Gunicorn (production WSGI server)
CMD ["gunicorn", "deployment.api.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
