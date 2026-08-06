"""
Whisper transcription service.

IMPORTANT (deployment fix):
`whisper` transitively imports `torch`, and `whisper.load_model(...)` downloads
and loads real model weights into memory. Previously this ran at MODULE IMPORT
TIME, which means it executed the moment `app.main` was imported - i.e. before
uvicorn even started binding to $PORT. On Railway/Render that made the
container blow past the health-check window (and, combined with TensorFlow/
DeepFace also loading eagerly, blow past the memory limit) before the server
ever came up. That's why Render OOM'd and Railway showed "no logs" - the
process was killed during import, before Python got a chance to flush stdout.

Fix: lazy-load the model on first actual use, cached afterwards.
"""

import os
import threading

_WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")

_model = None
_model_lock = threading.Lock()


def _get_model():
    """Load (and cache) the Whisper model on first use only."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # double-checked locking
                import whisper  # heavy import (pulls in torch) deferred until needed
                _model = whisper.load_model(_WHISPER_MODEL_NAME)
    return _model


def transcribe_audio(audio_path: str) -> str:
    model = _get_model()
    result = model.transcribe(audio_path)
    return result["text"]