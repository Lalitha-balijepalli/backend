# ============================================================================
# Interview Pro AI - backend/Dockerfile
#
# Multi-stage build:
#   Stage 1 "builder": installs build tools + compiles/downloads all Python
#                       deps into an isolated virtualenv.
#   Stage 2 "runtime":  copies ONLY the finished virtualenv + app code into a
#                       clean slim image.
#
# Architecture note: this backend no longer runs TensorFlow/Torch/DeepFace/
# Whisper locally - emotion detection and transcription call the Gemini API
# instead (see app/services/emotion_service.py and whisper_service.py). That
# means no OS-level ML libs (ffmpeg, libGL, X11 libs, compilers) are needed
# at runtime anymore - the whole stack is pure-Python HTTP clients, which is
# what actually gets this comfortably under Render free tier's 512MB.
# ============================================================================

# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Build-time only OS deps, kept in case any transitive dependency needs to
# compile from source on a given architecture. Discarded before the runtime
# stage regardless, so this costs nothing in the final image.
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
# `docker run` where $PORT isn't set. Single worker keeps memory predictable.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
