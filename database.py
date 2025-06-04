from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()

SQLITE_URL = "sqlite:///instance/healthtrack.db"  
engine = create_engine(
    SQLITE_URL, 
    echo=True, 
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database and create tables"""
    
    from models.user import User
    from models.food_entry import FoodEntry
    from models.goal import Goal
    
    Base.metadata.create_all(bind=engine)
    print("DEBUG: Tables created!")