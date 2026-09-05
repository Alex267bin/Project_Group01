import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


database_url = os.getenv("DATABASE_URL")
engine: Engine | None = create_engine(database_url) if database_url else None
SessionLocal: sessionmaker[Session] | None = (
    sessionmaker(bind=engine) if engine else None
)