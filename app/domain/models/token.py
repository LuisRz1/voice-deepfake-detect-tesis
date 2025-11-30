# token.py
from sqlmodel import SQLModel, Field, Column
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Enum as SAEnum  # para columna enum SQL
# Si prefieres que sea VARCHAR y no enum nativo, usa native_enum=False

class TokenType(str, Enum):
    verify_email = "verify_email"
    reset_password = "reset_password"

class OneTimeToken(SQLModel, table=True):
    __tablename__ = "one_time_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token: str = Field(index=True, nullable=False)  # UUID textual
    # Mapea el Enum a columna SQL (puedes poner native_enum=False si quieres VARCHAR)
    type: TokenType = Field(sa_column=Column(SAEnum(TokenType, name="token_type", native_enum=False), nullable=False))
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
