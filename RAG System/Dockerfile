# syntax=docker/dockerfile:1
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10

WORKDIR /app

# Build tools are only needed if a dependency (e.g. chromadb) has no wheel.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch first (a few hundred MB instead of several GB of CUDA libraries).
# --extra-index-url means pip falls back to the normal PyPI torch if no CPU wheel exists.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch==2.14.0 --extra-index-url https://download.pytorch.org/whl/cpu

# Everything else. The pip cache mount keeps downloaded wheels between build attempts.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .

# Run as a non-root user; /app/data is where persistent files should live.
RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]  