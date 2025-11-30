from typing import Protocol, List
from app.domain.models.audio import Audio

class IAudioRepository(Protocol):
    def save(self, audio: Audio) -> Audio: ...
    def get_all(self) -> List[Audio]: ...
    def get_by_user(self, user_id: int) -> List[Audio]: ...   # << antes era por device