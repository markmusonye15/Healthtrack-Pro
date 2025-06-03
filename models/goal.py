## Nutritional goals model
from sqlalchemy import Column, Integer, ForeignKey, Float  
from sqlalchemy.orm import relationship
from .base import Base

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True)
    daily_calories = Column(Integer)
    weekly_calories = Column(Integer)
    protein_goal = Column(Float)  
    carb_goal = Column(Float)     
    fat_goal = Column(Float)     
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    
    user = relationship("User", back_populates="goals")