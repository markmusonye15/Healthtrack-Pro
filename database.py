from models import FoodEntry, User, Goal  # Ensures tables are registered
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLITE_URL = "sqlite:///./healthtrack.db"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False}  # SQLite-specific
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)