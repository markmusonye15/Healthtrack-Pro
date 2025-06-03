# Initialization script for the database
from database import engine, Base
from models.user import User
from models.food_entry import FoodEntry
from models.goal import Goal

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")

if __name__ == "__main__":
    init_db()