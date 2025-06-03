from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class Audio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    result: str
    authenticity_score: float
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: str  # nuevo campo para vincular el audio con el dispositivo