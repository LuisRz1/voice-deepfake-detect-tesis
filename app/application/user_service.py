import uuid, os
from typing import Tuple, List, Optional
from datetime import datetime, timedelta, timezone
from email_validator import validate_email, EmailNotValidError
from fastapi import HTTPException

from app.domain.models.user import User
from app.domain.models.session import Session
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.session_repository import ISessionRepository
from app.domain.repositories.token_repository import ITokenRepository
from app.domain.models.token import OneTimeToken, TokenType

from app.infrastructure.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
)

class UserService:
    def __init__(self, users: IUserRepository, sessions: ISessionRepository, tokens: ITokenRepository):
        self.users = users
        self.sessions = sessions
        self.tokens = tokens

    # ------------ Registro & verificación ------------
    def register(self, email: str, password: str) -> User:
        try:
            validate_email(email)
        except EmailNotValidError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if self.users.get_by_email(email):
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(email=email, hashed_password=hash_password(password))
        return self.users.create(user)

    def create_email_verification(self, user_id: int) -> OneTimeToken:
        token = OneTimeToken(
            user_id=user_id,
            token=str(uuid.uuid4()),
            type=TokenType.verify_email,  # Enum
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("VERIFY_MIN", "30"))),
        )
        return self.tokens.create(token)

    def verify_email(self, token_str: str) -> None:
        t = self.tokens.get_valid(token_str, TokenType.verify_email)  # Enum
        if not t:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        user = self.users.get_by_id(t.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_verified:
            user.is_verified = True
            self.users.update(user)
        self.tokens.mark_used(t)

    # ------------ Login / Refresh / Logout ------------
    def login(self, email: str, password: str, user_agent: Optional[str], ip: Optional[str]):
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Inactive user")
        # si quieres exigir verificación antes de login, descomenta:
        # if not user.is_verified:
        #     raise HTTPException(status_code=403, detail="Email not verified")

        jti = str(uuid.uuid4())  # OK usar UUID como identificador opaco de la sesión
        refresh_exp = datetime.now(timezone.utc) + timedelta(days=int(os.getenv("REFRESH_DAYS", "7")))
        _ = self.sessions.create(Session(
            user_id=user.id, jti=jti, user_agent=user_agent, ip=ip, expires_at=refresh_exp
        ))
        # >>> ojo: user.id como int, NO str
        access = create_access_token(user.id, jti)
        refresh = create_refresh_token(user.id, jti)
        return user, access, refresh

    def refresh(self, refresh_token: str):
        from app.infrastructure.security import decode_token
        data = decode_token(refresh_token)
        if data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        jti = data.get("sid")
        sess = self.sessions.get_by_jti(jti)
        if (not sess) or (sess.revoked_at is not None) or (sess.expires_at <= datetime.now(timezone.utc)):
            raise HTTPException(status_code=401, detail="Session expired or revoked")
        # sub se guardó como int en el JWT; create_access_token espera int
        access = create_access_token(int(data["sub"]), jti)
        return access

    def revoke_current(self, jti: str):
        self.sessions.revoke(jti)

    def revoke_all(self, user_id: int):
        self.sessions.revoke_all_for_user(user_id)

    # ------------ Password reset ------------
    def create_reset(self, email: str) -> OneTimeToken:
        user = self.users.get_by_email(email)
        # Devuelve 200 aunque el correo no exista (evita enumeración)
        if not user:
            raise HTTPException(status_code=200, detail="If the email exists, a reset link will be sent")
        token = OneTimeToken(
            user_id=user.id,
            token=str(uuid.uuid4()),
            type=TokenType.reset_password,  # Enum
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("RESET_MIN", "30"))),
        )
        return self.tokens.create(token)

    def reset_password(self, token_str: str, new_password: str):
        t = self.tokens.get_valid(token_str, TokenType.reset_password)  # Enum
        if not t:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        user = self.users.get_by_id(t.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.hashed_password = hash_password(new_password)
        self.users.update(user)
        self.tokens.mark_used(t)

    def change_password(self, user: User, current: str, new: str):
        if not verify_password(current, user.hashed_password):
            raise HTTPException(status_code=400, detail="Wrong current password")
        user.hashed_password = hash_password(new)
        self.users.update(user)
