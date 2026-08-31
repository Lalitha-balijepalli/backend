"""
Facial emotion-detection service.

Formerly ran DeepFace (TensorFlow) locally, first with eager loading, then
with a lazy-loading fix. Lazy loading reduced *startup* memory, but the
first real request still had to load TensorFlow + DeepFace's model into
memory on top of the already-running app, contributing to Render free
tier's 512MB OOM kills (confirmed in production logs).

Now classifies emotion via the Gemini API (vision) instead. Function
name/signature (`detect_emotion(path) -> dict`) and return shape are
unchanged so app/routes/emotion.py and the frontend need no changes:
    {"dominant_emotion": str, "scores": {emotion: float, ...}}
on success, or {"error": str} on failure - exactly like before.
"""

import json
import mimetypes
import pathlib
import re

from app.services.gemini_client import get_model

# Same emotion label set DeepFace used, so downstream consumers (frontend,
# scoring logic) see the same keys as before.
_EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

_EMOTION_PROMPT = (
    "Look at the face in this image and classify the person's emotion. "
    "Respond with ONLY a JSON object (no markdown fences, no commentary) "
    "in exactly this shape:\n"
    '{"dominant_emotion": "<one of: angry, disgust, fear, happy, sad, surprise, neutral>", '
    '"scores": {"angry": <0-100>, "disgust": <0-100>, "fear": <0-100>, "happy": <0-100>, '
    '"sad": <0-100>, "surprise": <0-100>, "neutral": <0-100>}}\n'
    "The scores should reflect your confidence for each emotion and do not need to sum to exactly 100."
)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def detect_emotion(image_path: str) -> dict:
    try:
        path = pathlib.Path(image_path)
        mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        image_bytes = path.read_bytes()

        model = get_model()
        response = model.generate_content(
            [
                {"mime_type": mime_type, "data": image_bytes},
                _EMOTION_PROMPT,
            ]
        )

        raw_text = _JSON_FENCE_RE.sub("", response.text or "").strip()
        result = json.loads(raw_text)

        dominant_emotion = str(result["dominant_emotion"]).lower()
        scores = {
            label: float(result.get("scores", {}).get(label, 0.0))
            for label in _EMOTION_LABELS
        }

        return {
            "dominant_emotion": dominant_emotion,
            "scores": scores,
        }

    except Exception as e:
        return {
            "error": str(e)
        }
