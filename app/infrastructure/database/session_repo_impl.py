# app/infrastructure/database/session_repo_impl.py
from app.domain.models.session import Session
from app.domain.repositories.session_repository import ISessionRepository
from app.infrastructure.database.connection import get_session
from sqlmodel import select
from datetime import datetime, timezone
from typing import List, Optional

class SQLSessionRepository(ISessionRepository):
    def create(self, s: Session) -> Session:
        with get_session() as db:
            db.add(s)
            db.commit()
            db.refresh(s)
            return s

    def get_by_jti(self, jti: str) -> Optional[Session]:
        with get_session() as db:
            stmt = select(Session).where(Session.jti == jti)
            return db.exec(stmt).first()

    def revoke(self, jti: str) -> None:
        with get_session() as db:
            stmt = select(Session).where(Session.jti == jti)
            s = db.exec(stmt).first()
            if s:
                s.revoked_at = datetime.now(timezone.utc)
                db.add(s)
                db.commit()

    def revoke_all_for_user(self, user_id: int) -> None:
        with get_session() as db:
            stmt = select(Session).where(Session.user_id == user_id, Session.revoked_at.is_(None))
            for s in db.exec(stmt).all():
                s.revoked_at = datetime.now(timezone.utc)
                db.add(s)
            db.commit()

    def list_active_for_user(self, user_id: int) -> List[Session]:
        with get_session() as db:
            stmt = select(Session).where(Session.user_id == user_id).order_by(Session.created_at.desc())
            return list(db.exec(stmt).all())
