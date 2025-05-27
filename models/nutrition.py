## We will have food entry + Meal plan 


from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import validates
from .base import Base

class FoodEntry(Base):
    __tablename__ = "food_entries"
    __table_args__ = (
        CheckConstraint('calories >= 0', name='non_negative_calories'),
    )
    
    @validates('protein', 'carbs', 'fats')
    def validate_macros(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value