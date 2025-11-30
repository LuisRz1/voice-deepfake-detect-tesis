from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True)  # INT
    user_id: int = Field(foreign_key="users.id", index=True)
    jti: str = Field(index=True, nullable=False)   # id único del refresh
    user_agent: Optional[str] = None
    ip: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    revoked_at: Optional[datetime] = None
