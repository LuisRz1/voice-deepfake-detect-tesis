from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from app.infrastructure.model_loader import model, processor
from app.infrastructure.database.audio_repo_impl import SQLAudioRepository
from app.application.audio_service import AudioService
from app.application.schemas.audio_response import AudioResponse, AudioListItem
from app.infrastructure.security import get_current_user
from app.domain.models.user import User

router = APIRouter()
service = AudioService(SQLAudioRepository(), model, processor)

@router.post("/predict-audio", response_model=AudioResponse)
async def predict_audio(
    file: UploadFile = File(...),
    device_id: Optional[str] = Form(None),            # ← opcional
    user: User = Depends(get_current_user),           # ← tomado del access token
):
    try:
        audio, duration = await service.predict_audio(
            file=file,
            user_id=user.id,
            device_id=device_id,
        )
        return AudioResponse(
            id=audio.id,
            message=(
                "El audio tiene altas probabilidades de haber sido generado por IA"
                if audio.result == "falso" else
                "El audio parece ser original"
            ),
            authenticity_score=audio.authenticity_score,
            filename=audio.filename,
            result=audio.result,
            timestamp=audio.created,
            duration=round(duration, 2),
            model_name="SpecRNet",
            inference_start=audio.inference_start,
            inference_end=audio.inference_end,
            inference_duration=audio.inference_duration,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audios", response_model=List[AudioListItem])
def get_audios(user: User = Depends(get_current_user)):
    """Lista los audios del usuario autenticado."""
    try:
        audios = service.get_audios_by_user(user.id)
        return [
            AudioListItem(
                id=a.id,
                filename=a.filename,
                result=a.result,
                authenticity_score=a.authenticity_score,
                inference_duration=a.inference_duration,
                timestamp=a.created,
            )
            for a in audios
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
