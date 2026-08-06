import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# NOTE: none of the route modules below import TensorFlow / Torch / DeepFace /
# Whisper at module scope anymore - those heavy libraries are now lazy-loaded
# inside the relevant service functions on first actual use (see
# app/services/whisper_service.py and app/services/emotion_service.py).
# This keeps process startup fast and memory-light, which is required for
# Railway/Render health checks to succeed before their startup timeout.
from app.routes import emotion
from app.routes import speech
from app.routes.resume import router as resume_router
from app.routes.interview import router as interview_router
from app.routes.evaluation import router as evaluation_router
from app.routes.report import router as report_router
from app.routes import analysis
from app.routes import monitor
from app.routes import scoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("interview_pro_ai")

app = FastAPI(title="Interview Pro AI Backend")


@app.on_event("startup")
async def on_startup() -> None:
    # Deliberately does NOT touch TensorFlow/Torch/DeepFace/Whisper - those
    # stay lazy until an endpoint that needs them is actually called.
    logger.info("Interview Pro AI backend started - AI models are lazy-loaded on first use.")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",   # For development only
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Speech
app.include_router(
    speech.router,
    prefix="/speech",
    tags=["Speech"]
)

# Resume
app.include_router(
    resume_router,
    prefix="/resume",
    tags=["Resume"]
)

# Interview
app.include_router(
    interview_router,
    prefix="/interview",
    tags=["Interview"]
)

# Evaluation
app.include_router(
    evaluation_router,
    prefix="/evaluation",
    tags=["Evaluation"]
)

# Report
app.include_router(
    report_router,
    prefix="/report",
    tags=["Report"]
)

app.include_router(
    emotion.router,
    prefix="/emotion",
    tags=["Emotion Detection"]
)

app.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Analysis"]
)

app.include_router(
    monitor.router,
    prefix="/monitor",
    tags=["Live Monitoring"]
)

app.include_router(
    scoring.router,
    prefix="/scoring",
    tags=["Scoring"]
)

@app.get("/")
def root():
    return {"status": "ok", "service": "Interview Pro AI Backend"}


@app.get("/health")
def health_check():
    # Lightweight, dependency-free endpoint for Railway / Render health checks.
    return {"status": "ok"}