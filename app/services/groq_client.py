"""
Shared Groq API configuration.

Why Groq instead of Gemini:
- Repeated friction getting a working Gemini API key, plus a model-name
  retirement (gemini-2.0-flash -> gemini-3.6-flash) mid-project.
- Groq hosts OpenAI's real Whisper large-v3 model for transcription - actual
  purpose-built ASR, not an LLM approximating a transcript - with a generous
  free tier and no credit card required.
- Groq's API is OpenAI-compatible, so we call it with plain `requests` -
  no new heavy SDK dependency, keeping memory usage exactly where the
  Gemini migration got it (well under Render free tier's 512MB).

Get a free key at https://console.groq.com/keys and set GROQ_API_KEY in
your environment (see .env.example).
"""

import os

GROQ_API_BASE = "https://api.groq.com/openai/v1"

# Whisper large-v3 is Groq's standard hosted transcription model - stable
# and unlikely to be renamed (it mirrors OpenAI's own model naming).
TRANSCRIBE_MODEL = os.getenv("GROQ_TRANSCRIBE_MODEL", "whisper-large-v3")

# Vision-capable chat model for emotion classification. Groq's vision model
# lineup rotates more often than Whisper does - llama-3.2-11b-vision-preview
# (the original default) was retired, then its successor
# meta-llama/llama-4-scout-17b-16e-instruct was ALSO retired. Confirmed
# current model via https://console.groq.com/docs/vision : qwen/qwen3.6-27b
# (qwen/qwen3.8-27b is a newer alternative, capped at 3 images/request vs
# qwen3.6-27b's 5). If this 404s/decommissions again, check that docs page
# and set GROQ_VISION_MODEL in your environment to override - no code
# change needed.
VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")


class GroqNotConfiguredError(RuntimeError):
    """Raised when GROQ_API_KEY is missing from the environment."""


def get_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GroqNotConfiguredError(
            "GROQ_API_KEY is not set. Add it in your Render/Railway "
            "environment variables (see backend/.env.example). "
            "Get a free key at https://console.groq.com/keys"
        )
    return api_key
