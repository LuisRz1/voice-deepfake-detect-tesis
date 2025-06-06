from typing import List
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

    def get_all(self) -> List[Audio]:
        try:
            with get_session() as session:
                return session.query(Audio).order_by(Audio.created.desc()).all()
        except Exception as e:
            print(f"[ERROR] Fetching audios failed: {e}")
            raise

    def get_by_device(self, device_id: str) -> List[Audio]:
        try:
            with get_session() as session:
                return (
                    session.query(Audio)
                    .filter(Audio.device_id == device_id)
                    .order_by(Audio.created.desc())
                    .all()
                )
        except Exception as e:
            print(f"[ERROR] Fetching audios by device_id failed: {e}")
            raise