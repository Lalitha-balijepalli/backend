from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AnalysisRequest(BaseModel):
    transcription: str
    emotion: dict


@router.post("/analyze")
def analyze(data: AnalysisRequest):

    transcript = data.transcription.lower()

    filler_words = [
        "um",
        "uh",
        "like",
        "actually",
        "basically",
        "you know"
    ]

    filler_count = 0

    for word in filler_words:
        filler_count += transcript.count(word)

    word_count = len(transcript.split())

    speaking_score = max(0, 10 - filler_count)

    dominant = data.emotion.get("dominant_emotion", "neutral")

    confidence_score = 10

    if dominant in ["fear", "sad"]:
        confidence_score = 5

    elif dominant == "neutral":
        confidence_score = 7

    elif dominant == "happy":
        confidence_score = 10

    return {
        "word_count": word_count,
        "filler_words": filler_count,
        "speaking_score": speaking_score,
        "confidence_score": confidence_score,
        "dominant_emotion": dominant
    }