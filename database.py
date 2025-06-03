  # Ensures tables are registered
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base  

SQLITE_URL = "sqlite:///healthtrack.db"
engine = create_engine(SQLITE_URL, echo=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    
    from models.user import User
    from models.food_entry import FoodEntry
    from models.goal import Goal
    Base.metadata.create_all(bind=engine)
    print("DEBUG: Tables created!")