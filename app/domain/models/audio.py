from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class Audio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    result: str
    authenticity_score: float
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: str  # Identificador del dispositivo que envió el audio

    # Nuevos campos para registrar el tiempo de inferencia
    inference_start: Optional[datetime] = None  # Cuándo comenzó la inferencia
    inference_end: Optional[datetime] = None    # Cuándo terminó
    inference_duration: Optional[float] = None  # Duración total en segundos