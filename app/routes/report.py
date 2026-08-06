from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_report_status() -> dict[str, str]:
    return {"message": "report route ready"}
