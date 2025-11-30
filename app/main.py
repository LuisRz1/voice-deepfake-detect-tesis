from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.infrastructure.database.connection import create_db_and_tables
from app.infrastructure.routes.audio import router as audio_router
from app.infrastructure.routes.user import router as auth_router
from app.config import Settings

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Deepfake Detection API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(audio_router, prefix="", tags=["Audio Detection"])

@app.get("/health")
def health():
    return {"status": "ok"}
