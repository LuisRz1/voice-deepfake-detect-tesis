from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class Audio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    result: str
    confidence: float
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))