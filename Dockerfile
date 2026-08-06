# ============================================================================
# Interview Pro AI - backend/Dockerfile
#
# Multi-stage build:
#   Stage 1 "builder": installs build tools + compiles/downloads all Python
#                       deps into an isolated virtualenv.
#   Stage 2 "runtime":  copies ONLY the finished virtualenv + app code into a
#                       clean slim image. gcc/g++/pip caches/apt lists never
#                       make it into the final image.
#
# Why this matters for Railway/Render:
#   - The old single-stage Dockerfile kept gcc, g++, apt lists and pip's
#     build cache in the FINAL image, inflating image size for no runtime
#     benefit and slowing every deploy.
#   - AI models (TensorFlow/DeepFace/Torch/Whisper) are lazy-loaded by the
#     application code itself (see app/services/*.py) - NOT at import time -
#     so `uvicorn` binds to $PORT within a second or two of container start,
#     which is what Railway/Render's health check needs to see.
# ============================================================================

# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Build-time only OS deps (compilers for any package without a prebuilt wheel).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create an isolated venv so stage 2 can copy it wholesale.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime-only OS deps actually needed by opencv/deepface/ffmpeg-based audio
# handling. No compilers here - keeps the final image lean.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Bring in the fully-built virtualenv from the builder stage.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python runtime behaviour: no .pyc clutter, unbuffered logs so Railway/
# Render log streaming shows output immediately (critical for debugging
# startup issues instead of seeing "no logs" as before).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY . .

# Run as non-root for security.
RUN useradd --create-home appuser && \
    mkdir -p /app/uploads && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Railway/Render inject $PORT at runtime; default to 8000 for local
# `docker run` where $PORT isn't set. Single worker keeps memory predictable
# (each extra uvicorn worker would load its own copy of any AI model that
# gets lazy-loaded, multiplying memory usage).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
