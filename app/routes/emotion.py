from fastapi import APIRouter, UploadFile, File
import os

from app.services.emotion_service import detect_emotion

router = APIRouter()


@router.post("/detect")
async def detect(file: UploadFile = File(...)):

    os.makedirs("uploads", exist_ok=True)

    filepath = f"uploads/{file.filename}"

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    return detect_emotion(filepath)