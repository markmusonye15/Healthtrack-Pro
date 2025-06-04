from datetime import date
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.orm import relationship, validates
from database import Base
 
  # Imported for type hints

class FoodEntry(Base):
    
    __tablename__ = "food_entries"
    


    # Core Fields
    id = Column(Integer, primary_key=True)
    food_name = Column(String(100), nullable=False)
    calories = Column(Integer, nullable=False)
    date = Column(Date, default=date.today(), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Macronutrients (optional)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    
    # Relationships
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="food_entries")

    # Validation
    @validates('calories', 'protein', 'carbs', 'fats')
    def validate_nutrition(self, key, value):
        if value is None:
            return 0.0
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return round(value, 1) if isinstance(value, float) else value

    def __repr__(self):
        return f"<FoodEntry {self.food_name} ({self.calories} kcal)>"

    @property
    def macros(self):
        """Returns macronutrients as a dict"""
        return {
            'protein': self.protein,
            'carbs': self.carbs,
            'fats': self.fats
        }
    user = relationship("User", back_populates="food_entries")