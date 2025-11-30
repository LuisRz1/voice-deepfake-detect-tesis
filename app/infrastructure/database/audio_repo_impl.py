from typing import List, Optional
from sqlmodel import select
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
                stmt = select(Audio).order_by(Audio.created.desc())
                return session.exec(stmt).all()
        except Exception as e:
            print(f"[ERROR] Fetching audios failed: {e}")
            raise

    # 🔁 Nuevo: filtra por usuario
    def get_by_user(self, user_id: int) -> List[Audio]:
        try:
            with get_session() as session:
                stmt = (
                    select(Audio)
                    .where(Audio.user_id == user_id)
                    .order_by(Audio.created.desc())
                )
                return session.exec(stmt).all()
        except Exception as e:
            print(f"[ERROR] Fetching audios by user_id failed: {e}")
            raise

    # (Opcional) Si aún quieres combinar usuario + dispositivo:
    def get_by_user_and_device(self, user_id: int, device_id: str) -> List[Audio]:
        try:
            with get_session() as session:
                stmt = (
                    select(Audio)
                    .where(Audio.user_id == user_id, Audio.device_id == device_id)
                    .order_by(Audio.created.desc())
                )
                return session.exec(stmt).all()
        except Exception as e:
            print(f"[ERROR] Fetching audios by user_id and device_id failed: {e}")
            raise
