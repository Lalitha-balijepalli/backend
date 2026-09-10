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

    try:
        text = transcribe_audio(filepath)
    except Exception as e:
        # Return the real Groq error in the response body (visible in the
        # docs UI / curl output directly) instead of a bare 500 that
        # requires digging through Render logs.
        return {"error": str(e)}

    return {
        "transcription": text
    }