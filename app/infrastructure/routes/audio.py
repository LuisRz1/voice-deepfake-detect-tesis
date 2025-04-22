from fastapi import APIRouter, UploadFile, File, HTTPException
from app.application.audio_service import predict_audio
from app.application.schemas.audio_response import AudioResponse

router = APIRouter()

@router.post("/predict-audio", response_model=AudioResponse)
async def predict(file: UploadFile = File(...)):
    try:
        audio = await predict_audio(file)
        print("[DEBUG] Atributos del objeto audio:", dir(audio))
        return AudioResponse(
            message=("High probability of AI-generated audio"
                     if audio.result == "fake" else
                     "Low probability of AI-generated audio"),
            confidence=audio.confidence,
            filename=audio.filename,
            result=audio.result,
            timestamp=audio.created
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))