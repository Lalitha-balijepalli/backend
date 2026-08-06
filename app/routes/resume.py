from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_resume_status() -> dict[str, str]:
    return {"message": "resume route ready"}
