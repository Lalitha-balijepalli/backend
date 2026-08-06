from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class EvaluationRequest(BaseModel):
    question: str
    answer: str

@router.post("/evaluate")
def evaluate_answer(data: EvaluationRequest):

    return {
        "question": data.question,
        "answer": data.answer,
        "message": "Evaluation is handled by Lovable frontend Gemini"
    }