from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class Audio(SQLModel, table=True):
    __tablename__ = "audios"

    id: Optional[int] = Field(default=None, primary_key=True)
    # Relación: audio pertenece a un usuario
    user_id: int = Field(foreign_key="users.id", index=True)   # << NUEVO
    filename: str
    result: str
    authenticity_score: float
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # opcional: si aún quieres rastrear el equipo, mantenlo como nullable
    device_id: Optional[str] = None

    # Tiempos de inferencia
    inference_start: Optional[datetime] = None
    inference_end: Optional[datetime] = None
    inference_duration: Optional[float] = None
