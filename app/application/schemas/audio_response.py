from pydantic import BaseModel
from datetime import datetime

class AudioResponse(BaseModel):
    id: int
    message: str
    authenticity_score: float
    filename: str
    result: str
    timestamp: datetime
    duration: float
    model_name: str

class AudioListItem(BaseModel):
    id: int
    filename: str
    result: str
    authenticity_score: float
    timestamp: datetime