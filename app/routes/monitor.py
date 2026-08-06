from fastapi import APIRouter, UploadFile, File
import os

from app.services.analysis_service import analyze_candidate

router = APIRouter()

@router.post("/live")
async def live_monitor(file: UploadFile = File(...)):

    os.makedirs("uploads", exist_ok=True)

    filepath = f"uploads/{file.filename}"

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    result = analyze_candidate(filepath)

    return result