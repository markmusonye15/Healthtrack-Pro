## User Model (1 to many relationships)
from sqlalchemy import Column, Integer, String
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    
    # No relationships yet (we'll add them later)