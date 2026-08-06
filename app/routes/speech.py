from fastapi import APIRouter, UploadFile, File
import os

from app.services.whisper_service import transcribe_audio

router = APIRouter()

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):

    os.makedirs("uploads", exist_ok=True)

    filepath = f"uploads/{file.filename}"

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    text = transcribe_audio(filepath)

    return {
        "transcription": text
    }