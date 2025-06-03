## Nutritional goals model
from sqlalchemy import Column, Integer, ForeignKey
from .base import BaseModel

class Goal(BaseModel):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True)
    daily_calories = Column(Integer)
    weekly_calories = Column(Integer)
    
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)