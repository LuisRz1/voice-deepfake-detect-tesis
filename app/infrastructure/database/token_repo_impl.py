# app/infrastructure/database/token_repo_impl.py
from typing import Optional
from sqlmodel import select
from datetime import datetime, timezone
from app.domain.repositories.token_repository import ITokenRepository
from app.domain.models.token import OneTimeToken, TokenType
from app.infrastructure.database.connection import get_session

def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

class SQLTokenRepository(ITokenRepository):
    def create(self, t: OneTimeToken) -> OneTimeToken:
        with get_session() as s:
            s.add(t); s.commit(); s.refresh(t)
            return t

    def get_valid(self, token: str, token_type: TokenType) -> Optional[OneTimeToken]:
        tok = (token or "").strip()
        with get_session() as s:
            t = s.exec(
                select(OneTimeToken).where(
                    OneTimeToken.token == tok,
                    OneTimeToken.type == token_type,
                )
            ).first()

            if not t:
                return None

            now = _aware(datetime.now(timezone.utc))
            exp = _aware(t.expires_at)
            used = _aware(t.used_at)

            if used is not None:
                return None
            if exp is None or exp <= now:
                return None

            return t

    def mark_used(self, t: OneTimeToken) -> None:
        with get_session() as s:
            t.used_at = _aware(datetime.now(timezone.utc))
            s.add(t); s.commit()
