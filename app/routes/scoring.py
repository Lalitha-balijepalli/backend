from fastapi import APIRouter
from pydantic import BaseModel

from app.services.scoring_service import calculate_score

router = APIRouter()


class ScoreRequest(BaseModel):
    answer_score: float
    confidence: float
    attention: float
    emotion: str


@router.post("/calculate")
def calculate(data: ScoreRequest):

    return calculate_score(
        data.answer_score,
        data.confidence,
        data.attention,
        data.emotion
    )