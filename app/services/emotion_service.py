"""
DeepFace emotion-detection service.

IMPORTANT (deployment fix):
`from deepface import DeepFace` at module import time transitively imports
TensorFlow/tf_keras. Because `app/main.py` eagerly imports every route
(including this one via `emotion.py`), TensorFlow was previously being
imported the instant the app started - well before uvicorn bound to $PORT.
That's a multi-hundred-MB, multi-second cost paid on every single startup,
even for requests that never touch emotion detection, and it was a major
contributor to Railway's health-check timeout / Render's OOM kill.

Fix: defer the `deepface` import until `detect_emotion` is actually called,
and cache the imported module so the cost is paid once, lazily, on first use.
"""

import threading

_deepface_module = None
_import_lock = threading.Lock()


def _get_deepface():
    global _deepface_module
    if _deepface_module is None:
        with _import_lock:
            if _deepface_module is None:  # double-checked locking
                from deepface import DeepFace  # heavy import (pulls in TensorFlow) deferred
                _deepface_module = DeepFace
    return _deepface_module


def detect_emotion(image_path: str):
    try:
        DeepFace = _get_deepface()
        result = DeepFace.analyze(
            img_path=image_path,
            actions=["emotion"],
            detector_backend="opencv",
            enforce_detection=False
        )

        if isinstance(result, list):
            result = result[0]

        dominant_emotion = str(result["dominant_emotion"])

        emotions = {}

        for emotion, score in result["emotion"].items():
            emotions[emotion] = float(score)

        return {
            "dominant_emotion": dominant_emotion,
            "scores": emotions
        }

    except Exception as e:
        return {
            "error": str(e)
        }