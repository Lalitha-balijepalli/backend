"""
Facial emotion-detection service.

Now calls a Groq-hosted vision model instead of Gemini (see
app/services/groq_client.py for why). Function name/signature
(`detect_emotion(path) -> dict`) and return shape are unchanged so
app/routes/emotion.py and the frontend need no changes:
    {"dominant_emotion": str, "scores": {emotion: float, ...}}
on success, or {"error": str} on failure - exactly like before.
"""

import base64
import json
import mimetypes
import pathlib
import re

import requests

from app.services.groq_client import GROQ_API_BASE, VISION_MODEL, get_api_key

_CHAT_URL = f"{GROQ_API_BASE}/chat/completions"

# Same emotion label set the original DeepFace implementation used, so
# downstream consumers (frontend, scoring logic) see the same keys as before.
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
        image_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        data_url = f"data:{mime_type};base64,{image_b64}"

        response = requests.post(
            _CHAT_URL,
            headers={
                "Authorization": f"Bearer {get_api_key()}",
                "Content-Type": "application/json",
            },
            json={
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _EMOTION_PROMPT},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                # Qwen 3.6/3.8 on Groq support a "thinking" mode that can
                # consume the whole response on reasoning tokens, leaving
                # message.content empty (what we hit in testing). Asking for
                # low/no reasoning effort keeps the reply to just the final
                # JSON answer. If Groq's API uses a different parameter name
                # for this, the debug_raw_response below will show it.
                "reasoning_effort": "none",
                "temperature": 0,
            },
            timeout=60,
        )
        if response.status_code != 200:
            # Surface Groq's actual error body (e.g. "model has been
            # decommissioned") instead of requests' generic "400 Bad
            # Request" message, which has no diagnostic value on its own.
            return {"error": f"Groq API error {response.status_code}: {response.text}"}

        response_json = response.json()
        message = response_json["choices"][0]["message"]
        raw_text = (message.get("content") or "").strip()

        if not raw_text:
            # Empty content even after asking for no reasoning - surface the
            # full response so the actual shape (e.g. a separate "reasoning"
            # field, or a finish_reason of "length") is visible without
            # another round-trip through Render's logs.
            return {
                "error": "Groq returned empty content.",
                "debug_raw_response": response_json,
            }
        raw_text = _JSON_FENCE_RE.sub("", raw_text).strip()
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
