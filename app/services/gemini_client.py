"""
Shared Gemini API client.

Why this exists (deployment context):
Interview Pro AI originally ran DeepFace (TensorFlow) and Whisper (Torch)
locally for emotion detection and transcription. On Render's free tier
(512MB RAM), that combination reliably OOM-killed the instance on the very
first real request - confirmed in production logs ("Ran out of memory (used
over 512MB)"). No amount of lazy-loading fixes that; torch + a Whisper model
alone eat ~490MB by themselves, leaving no room for anything else.

Fix: emotion detection and transcription are now done via the Gemini API
(multimodal) instead of self-hosted models. This removes tensorflow, torch,
deepface, and openai-whisper from the dependency tree entirely, which is
what actually gets memory usage under the free-tier ceiling - lazy loading
alone could not.

`google-generativeai` itself is lightweight (no ML runtime bundled), so
importing it at module scope here is fine and does not reintroduce the
startup-cost problem that TensorFlow/Torch caused.
"""

import os
import threading

import google.generativeai as genai

_configured = False
_configure_lock = threading.Lock()

# Any current multimodal Gemini model works here; flash is fast/cheap and
# sufficient for transcription + single-image emotion classification.
#
# NOTE: gemini-2.0-flash was retired by Google after this was first written -
# a live 404 from the API named "gemini-3.6-flash" as the replacement. Google
# rotates model names periodically; if this default 404s again, check
# https://ai.google.dev/gemini-api/docs/models for the current lineup, or
# just set GEMINI_MODEL in your environment (Render/Railway dashboard) to
# override this without a code change.
_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


class GeminiNotConfiguredError(RuntimeError):
    """Raised when GEMINI_API_KEY is missing from the environment."""


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    with _configure_lock:
        if _configured:
            return
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiNotConfiguredError(
                "GEMINI_API_KEY is not set. Add it in your Render/Railway "
                "environment variables (see backend/.env.example)."
            )
        genai.configure(api_key=api_key)
        _configured = True


def get_model() -> "genai.GenerativeModel":
    """Return a ready-to-use Gemini GenerativeModel, configuring the SDK on first call."""
    _ensure_configured()
    return genai.GenerativeModel(_MODEL_NAME)
