# app/infrastructure/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from app.domain.models.user import User
from app.infrastructure.database.user_repo_impl import SQLUserRepository
from app.infrastructure.database.session_repo_impl import SQLSessionRepository

JWT_SECRET = "super-dev-secret-que-no-cambia"
JWT_ALG = "HS256"
ACCESS_MIN = 15
REFRESH_DAYS = 7

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(p: str) -> str:
    return pwd_context.hash(p)


def verify_password(p: str, hp: str) -> bool:
    return pwd_context.verify(p, hp)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Convierte datetimes naive a UTC-aware."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def create_access_token(user_id: int, session_jti: str) -> str:
    exp = _now() + timedelta(minutes=ACCESS_MIN)
    payload = {"sub": str(user_id), "sid": session_jti, "type": "access", "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def create_refresh_token(user_id: int, session_jti: str) -> str:
    exp = _now() + timedelta(days=REFRESH_DAYS)
    payload = {
        "sub": str(user_id),
        "sid": session_jti,
        "type": "refresh",
        "exp": exp,
        "jti": session_jti,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    data = decode_token(token)

    # debe ser access
    if data.get("type") != "access":
        raise HTTPException(status_code=401, detail="Wrong token type")

    # validar sesión en BD
    jti = data.get("sid")
    sess_repo = SQLSessionRepository()
    sess = sess_repo.get_by_jti(jti)
    now = _now()

    expires = _aware(sess.expires_at) if sess else None
    revoked = _aware(sess.revoked_at) if sess else None

    if (not sess) or (revoked is not None) or (expires is not None and expires <= now):
        # sesión no válida -> como si estuviera deslogueado
        raise HTTPException(status_code=401, detail="Session expired or revoked")

    # cargar usuario
    user_id = int(data["sub"])
    user = SQLUserRepository().get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user
