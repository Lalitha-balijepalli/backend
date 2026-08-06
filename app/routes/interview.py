from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

class InterviewRequest(BaseModel):
    role: str
    difficulty: str
    skills: list[str] = Field(default_factory=list)
    questions: list[str]

@router.post("/start")
def start_interview(data: InterviewRequest):

    return {
        "message": "Interview started successfully",
        "role": data.role,
        "difficulty": data.difficulty,
        "skills": data.skills,
        "questions": data.questions
    }