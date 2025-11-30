# user_response.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserPublic(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    created_at: datetime

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginResponse(BaseModel):
    user: UserPublic
    tokens: TokenPair

class SessionItem(BaseModel):
    id: int
    created_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip: Optional[str] = None
