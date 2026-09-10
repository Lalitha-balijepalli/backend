"""
Speech transcription service.

Now calls Groq's hosted Whisper large-v3 model instead of Gemini (see
app/services/groq_client.py for why). Function name/signature
(`transcribe_audio(path) -> str`) is unchanged so app/routes/speech.py needs
no changes.
"""

import mimetypes
import pathlib

import requests

from app.services.groq_client import GROQ_API_BASE, TRANSCRIBE_MODEL, get_api_key

_TRANSCRIBE_URL = f"{GROQ_API_BASE}/audio/transcriptions"


def transcribe_audio(audio_path: str) -> str:
    path = pathlib.Path(audio_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "audio/mpeg"

    with open(path, "rb") as f:
        response = requests.post(
            _TRANSCRIBE_URL,
            headers={"Authorization": f"Bearer {get_api_key()}"},
            files={"file": (path.name, f, mime_type)},
            data={"model": TRANSCRIBE_MODEL},
            timeout=120,
        )
    if response.status_code != 200:
        # Surface Groq's actual error body instead of a generic HTTPError,
        # so the real reason (e.g. a retired model name) is visible without
        # digging through Render's logs.
        raise RuntimeError(f"Groq API error {response.status_code}: {response.text}")
    return response.json().get("text", "").strip()
