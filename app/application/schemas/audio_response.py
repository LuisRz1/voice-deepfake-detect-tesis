from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AudioResponse(BaseModel):
    id: int
    message: str
    authenticity_score: float
    filename: str
    result: str
    timestamp: datetime
    duration: float  # ← Tiempo de inferencia en segundos
    model_name: str

    # Estos campos son opcionales por si necesitas trazabilidad más fina
    inference_start: Optional[datetime] = None
    inference_end: Optional[datetime] = None

class AudioListItem(BaseModel):
    id: int
    filename: str
    result: str
    authenticity_score: float
    timestamp: datetime