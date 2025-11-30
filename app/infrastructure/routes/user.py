from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, Depends, Request, BackgroundTasks
from fastapi import HTTPException, status
from typing import List
from app.application.user_service import UserService
from app.infrastructure.database.user_repo_impl import SQLUserRepository
from app.infrastructure.database.session_repo_impl import SQLSessionRepository
from app.infrastructure.database.token_repo_impl import SQLTokenRepository
from app.application.schemas.user_request import (
    RegisterInput, LoginInput, ForgotPasswordInput, ResetPasswordInput, ChangePasswordInput
)
from app.application.schemas.user_response import UserPublic, LoginResponse, TokenPair, SessionItem
from app.infrastructure.security import get_current_user, decode_token
from app.domain.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])

svc = UserService(SQLUserRepository(), SQLSessionRepository(), SQLTokenRepository())

# ---- Helpers: envío de correo (stub) ----
def send_email(to: str, subject: str, body: str):
    # Reemplaza por tu proveedor real (SendGrid, SES, SMTP).
    print(f"[EMAIL] To={to}\nSubject={subject}\n\n{body}\n")

@router.post("/register", response_model=UserPublic, status_code=201)
def register(payload: RegisterInput, bg: BackgroundTasks):
    user = svc.register(payload.email, payload.password)
    tok = svc.create_email_verification(user.id)
    verify_link = f"{'/'.join(['https://tu-frontend.com','verify'])}?token={tok.token}"
    bg.add_task(send_email, to=user.email, subject="Verify your account", body=f"Click: {verify_link}")
    return UserPublic(id=user.id, email=user.email, is_verified=user.is_verified, created_at=user.created_at)

@router.get("/verify-email")
def verify_email(token: str):
    # Normaliza: puede venir con espacios o como URL completa
    raw = (token or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        try:
            q = parse_qs(urlparse(raw).query)
            raw = (q.get("token", [None])[0] or "").strip()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid token URL")

    if not raw:
        raise HTTPException(status_code=400, detail="Missing token")

    svc.verify_email(raw)
    return {"message": "Email verified. You can login now."}

@router.post("/forgot-password")
def forgot(payload: ForgotPasswordInput, bg: BackgroundTasks):
    try:
        tok = svc.create_reset(payload.email)
        reset_link = f"{'/'.join(['https://tu-frontend.com','reset'])}?token={tok.token}"
        # 🔧 enviar al correo del payload (o al user.email), NO a user_id
        bg.add_task(send_email, to=payload.email, subject="Password reset", body=f"Reset: {reset_link}")
    except HTTPException:
        pass
    return {"message": "If the email exists, a reset link will be sent."}

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginInput, request: Request):
    ua = request.headers.get("user-agent"); ip = request.client.host if request.client else None
    user, access, refresh = svc.login(payload.email, payload.password, ua, ip)
    return LoginResponse(
        user=UserPublic(id=user.id, email=user.email, is_verified=user.is_verified, created_at=user.created_at),
        tokens={"access_token": access, "refresh_token": refresh},
    )

@router.post("/refresh", response_model=TokenPair)
def refresh(tokens: TokenPair):
    # solo necesitamos refresh_token; mantenemos shape compatible
    new_access = svc.refresh(tokens.refresh_token)
    return TokenPair(access_token=new_access, refresh_token=tokens.refresh_token)

@router.post("/logout")
def logout(tokens: TokenPair):
    data = decode_token(tokens.refresh_token)
    svc.revoke_current(data["sid"])
    return {"message": "Logged out from current session."}

@router.post("/logout-all")
def logout_all(user: User = Depends(get_current_user)):
    svc.revoke_all(user.id)
    return {"message": "All sessions revoked."}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordInput):
    svc.reset_password(payload.token, payload.new_password)
    return {"message": "Password updated."}

@router.post("/change-password")
def change_password(payload: ChangePasswordInput, user: User = Depends(get_current_user)):
    svc.change_password(user, payload.current_password, payload.new_password)
    return {"message": "Password changed."}

@router.get("/sessions", response_model=List[SessionItem])
def list_sessions(user: User = Depends(get_current_user)):
    from app.infrastructure.database.session_repo_impl import SQLSessionRepository
    repo = SQLSessionRepository()
    sessions = repo.list_active_for_user(user.id)
    return [
        SessionItem(
            id=s.id,
            created_at=s.created_at,
            expires_at=s.expires_at,
            revoked_at=s.revoked_at,
            user_agent=s.user_agent,
            ip=s.ip,
        )
        for s in sessions
    ]

