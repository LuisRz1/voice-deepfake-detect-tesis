from fastapi import APIRouter, UploadFile, File, HTTPException
from app.infrastructure.model_loader import model, processor
from app.infrastructure.database.audio_repo_impl import SQLAudioRepository
from app.application.audio_service import AudioService
from app.application.schemas.audio_response import AudioResponse

router = APIRouter()

service = AudioService(SQLAudioRepository(), model, processor)

@router.post("/predict-audio", response_model=AudioResponse)
async def predict(file: UploadFile = File(...)):
    try:
        audio = await service.predict_audio(file)
        return AudioResponse(
            message="El audio tiene altas probabilidades de haber sido generado por IA" if audio.result == "fake" else "El audio tiene altas probabilidades de ser auténtico",
            authenticity_score=audio.authenticity_score,
            filename=audio.filename,
            result=audio.result,
            timestamp=audio.created
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))