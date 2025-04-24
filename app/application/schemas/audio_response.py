from pydantic import BaseModel
from datetime import datetime

class AudioResponse(BaseModel):
    message: str
    authenticity_score: float
    filename: str
    result: str
    timestamp: datetime