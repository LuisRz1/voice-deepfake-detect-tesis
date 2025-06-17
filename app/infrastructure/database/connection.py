from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db")

# Para PostgreSQL se recomienda esto:
engine = create_engine(DATABASE_URL, echo=False, connect_args={})

def get_session():
    return Session(engine)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
