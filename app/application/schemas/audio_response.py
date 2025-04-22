from pydantic import BaseModel
from datetime import datetime

class AudioResponse(BaseModel):
    message: str
    confidence: float
    filename: str
    result: str
    timestamp: datetime