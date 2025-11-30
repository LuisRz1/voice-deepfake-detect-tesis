from pydantic.v1 import BaseSettings
from typing import List


class Settings(BaseSettings):
    # JWT
    JWT_SECRET: str = "dev-secret-change"
    ACCESS_MIN: int = 15
    REFRESH_DAYS: int = 7
    VERIFY_MIN: int = 30
    RESET_MIN: int = 30

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://10.0.2.2:8000",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_file = ".env"
