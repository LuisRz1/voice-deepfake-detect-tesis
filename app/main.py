from fastapi import FastAPI
from app.infrastructure.database.connection import create_db_and_tables
from app.infrastructure.routes.audio import router as audio_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Deepfake Detection API", lifespan=lifespan)
app.include_router(audio_router, prefix="", tags=["Audio Detection"])

