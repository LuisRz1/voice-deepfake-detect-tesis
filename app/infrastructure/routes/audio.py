from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.infrastructure.model_loader import model, processor
from app.infrastructure.database.audio_repo_impl import SQLAudioRepository
from app.application.audio_service import AudioService
from app.application.schemas.audio_response import AudioResponse, AudioListItem

router = APIRouter()

service = AudioService(SQLAudioRepository(), model, processor)

@router.post("/predict-audio", response_model=AudioResponse)
async def predict(file: UploadFile = File(...)):
    try:
        audio, duration = await service.predict_audio(file)
        return AudioResponse(
            id=audio.id,
            message="El audio tiene altas probabilidades de haber sido generado por IA" if audio.result == "fake"
                    else "El audio parece ser original",
            authenticity_score=audio.authenticity_score,
            filename=audio.filename,
            result=audio.result,
            timestamp=audio.created,
            duration=round(duration, 2),
            model_name="SpecRNet"  # o usa model.config._name_or_path si deseas extraer dinámicamente
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audios", response_model=List[AudioListItem])
async def get_all_audios():
    try:
        audios = service.get_all_audios()
        return [
            AudioListItem(
                id=a.id,
                filename=a.filename,
                result=a.result,
                authenticity_score=a.authenticity_score,
                timestamp=a.created
            )
            for a in audios
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))