from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URL = "sqlite:///./telemetry.db"

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},  # SQL plus FastAPI threaded
    future=True,    
)

SessionLocal= sessionmaker(bind=engine, autoflush=False,autocommit=False,future=True)

Base = declarative_base()

def init_db() -> None:
    #import models so tables are registered before create all
    from . import db_models #noqa: F401
    Base.metadata.create_all(bind=engine)