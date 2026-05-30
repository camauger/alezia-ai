# backend/database.py
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from backend.config import DB_PATH

SQLALCHEMY_DATABASE_URL = f'sqlite:///{DB_PATH}'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a SQLAlchemy session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
