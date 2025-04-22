from app.domain.repositories.audio_repository import IAudioRepository
from app.domain.models.audio import Audio
from app.infrastructure.database.connection import get_session

class SQLAudioRepository(IAudioRepository):
    def save(self, audio: Audio) -> Audio:
        try:
            with get_session() as session:
                session.add(audio)
                session.commit()
                session.refresh(audio)
                return audio
        except Exception as e:
            print(f"[ERROR] Saving audio failed: {e}")
            raise