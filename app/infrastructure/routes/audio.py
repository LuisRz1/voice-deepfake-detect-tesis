from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from app.infrastructure.model_loader import model, processor
from app.infrastructure.database.audio_repo_impl import SQLAudioRepository
from app.application.audio_service import AudioService
from app.application.schemas.audio_response import AudioResponse, AudioListItem

router = APIRouter()

service = AudioService(SQLAudioRepository(), model, processor)

@router.post("/predict-audio", response_model=AudioResponse)
async def predict(file: UploadFile = File(...), device_id: str = Form(...)):
    try:
        audio, duration = await service.predict_audio(file,device_id)
        print(
            f"Audio: {audio.filename} - Resultado: {audio.result} - Authenticidad: {audio.authenticity_score} - Tiempo: {audio.created}"
        )
        return AudioResponse(
            id=audio.id,
            message="El audio tiene altas probabilidades de haber sido generado por IA" if audio.result == "Falso" else "El audio parece ser original",
            authenticity_score=audio.authenticity_score,
            filename=audio.filename,
            result=audio.result,
            timestamp=audio.created,
            duration=round(duration, 2),
            model_name="SpecRNet",
            inference_start=audio.inference_start,
            inference_end=audio.inference_end,
            inference_duration=audio.inference_duration
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audios", response_model=List[AudioListItem])
async def get_audios(device_id: str = Query(...)):  # ← Se filtra por device_id
    try:
        audios = service.get_audios_by_device(device_id)
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