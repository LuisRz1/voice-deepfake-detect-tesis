from typing import Protocol
from app.domain.models.audio import Audio

class IAudioRepository(Protocol):
    def save(self, audio: Audio) -> Audio: ...