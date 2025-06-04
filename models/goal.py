## Nutritional goals model
from sqlalchemy import Column, Integer, ForeignKey, Float  
from sqlalchemy.orm import relationship
from .base import Base

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    daily_calories = Column(Integer)
    weekly_calories = Column(Integer)
   

    user = relationship("User", back_populates="goals")