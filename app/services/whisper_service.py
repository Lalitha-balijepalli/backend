"""
Speech transcription service.

Formerly ran openai-whisper (Torch) locally, first with eager loading, then
with a lazy-loading fix. Lazy loading reduced *startup* memory, but the
first real transcription request still had to load torch + the Whisper
model into memory on top of the already-running app, which reliably
exceeded Render free tier's 512MB ("Ran out of memory (used over 512MB)" in
production logs).

Now transcribes via the Gemini API instead. Function name/signature
(`transcribe_audio(path) -> str`) is unchanged so app/routes/speech.py needs
no changes.
"""

import mimetypes
import pathlib

from app.services.gemini_client import get_model

_TRANSCRIBE_PROMPT = (
    "Transcribe this audio recording exactly as spoken. "
    "Return ONLY the transcript text - no preamble, no commentary, "
    "no quotation marks, no markdown formatting."
)


def transcribe_audio(audio_path: str) -> str:
    path = pathlib.Path(audio_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "audio/mpeg"
    audio_bytes = path.read_bytes()

    model = get_model()
    response = model.generate_content(
        [
            {"mime_type": mime_type, "data": audio_bytes},
            _TRANSCRIBE_PROMPT,
        ]
    )
    return (response.text or "").strip()
