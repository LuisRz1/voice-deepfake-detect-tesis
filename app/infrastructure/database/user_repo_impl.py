from typing import Optional
from sqlmodel import select
from app.domain.repositories.user_repository import IUserRepository
from app.domain.models.user import User
from app.infrastructure.database.connection import get_session
import uuid

class SQLUserRepository(IUserRepository):
    def create(self, user: User) -> User:
        with get_session() as s:
            s.add(user); s.commit(); s.refresh(user)
            return user

    def get_by_email(self, email: str) -> Optional[User]:
        with get_session() as s:
            return s.exec(select(User).where(User.email == email)).first()

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        with get_session() as s:
            return s.get(User, user_id)

    def update(self, user: User) -> User:
        with get_session() as s:
            s.add(user); s.commit(); s.refresh(user)
            return user
