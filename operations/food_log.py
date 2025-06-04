from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Optional
from models.food_entry import FoodEntry

class FoodLogOps:
    def __init__(self, db: Session):
        self.db = db
    
    def log_meal(
        self, 
        user_id: int, 
        food_name: str, 
        calories: int, 
        meal_date: date = None,
    ) -> FoodEntry:
        """Log a food entry with automatic date handling
        
        Args:
            user_id: ID of the user
            food: Name of the food item
            calories: Calorie count
            meal_date: Date of the meal (defaults to today)
            meal_type: Type of meal (e.g., breakfast, lunch, dinner)
            
        Returns:
            The created FoodEntry object
            
        Raises:
            ValueError: If calories is negative
        """
        if calories < 0:
            raise ValueError("Calories cannot be negative")
            
        entry = FoodEntry(
            food_name=food_name,
            calories=calories,
            date=meal_date or date.today(),
            user_id=user_id,
            
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def get_daily_logs(self, user_id: int, target_date: date) -> List[FoodEntry]:
      
        """Get all food entries for a specific day (simplified without meal grouping)"""
        return self.db.query(FoodEntry).filter(
        FoodEntry.user_id == user_id,
        FoodEntry.date == target_date
    ).order_by(FoodEntry.id).all()
    
    def get_logs_in_range(
        self, 
        user_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[FoodEntry]:
        """Get all food entries within a date range (inclusive)
        
        Args:
            user_id: ID of the user
            start_date: Start date of range
            end_date: End date of range
            
        Returns:
            List of FoodEntry objects within the date range
        """
        return self.db.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            FoodEntry.date >= start_date,
            FoodEntry.date <= end_date
        ).order_by(FoodEntry.date, FoodEntry.id).all()
    
    def update_entry(
        self, 
        entry_id: int, 
        user_id: int, 
        food: Optional[str] = None,
        calories: Optional[int] = None,
        meal_date: Optional[date] = None,
        meal_type: Optional[str] = None
    ) -> Optional[FoodEntry]:
        """Update an existing food entry
        
        Args:
            entry_id: ID of the entry to update
            user_id: ID of the user (for verification)
            food: New food name (optional)
            calories: New calorie count (optional)
            meal_date: New date (optional)
            meal_type: New meal type (optional)
            
        Returns:
            The updated FoodEntry if found, None otherwise
        """
        entry = self.db.query(FoodEntry).filter(
            FoodEntry.id == entry_id,
            FoodEntry.user_id == user_id
        ).first()
        
        if entry:
            if food is not None:
                entry.food_name = food
            if calories is not None:
                if calories < 0:
                    raise ValueError("Calories cannot be negative")
                entry.calories = calories
            if meal_date is not None:
                entry.date = meal_date
            if meal_type is not None:
                entry.meal_type = meal_type
                
            self.db.commit()
            self.db.refresh(entry)
        
        return entry
    
    def delete_entry(self, entry_id: int, user_id: int) -> bool:
        """Delete a food entry
        
        Args:
            entry_id: ID of the entry to delete
            user_id: ID of the user (for verification)
            
        Returns:
            True if deletion was successful, False otherwise
        """
        entry = self.db.query(FoodEntry).filter(
            FoodEntry.id == entry_id,
            FoodEntry.user_id == user_id
        ).first()
        
        if entry:
            self.db.delete(entry)
            self.db.commit()
            return True
        return False
    
    def get_recent_logs(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> List[FoodEntry]:
        """Get most recent food entries
        
        Args:
            user_id: ID of the user
            limit: Maximum number of entries to return
            
        Returns:
            List of recent FoodEntry objects
        """
        return self.db.query(FoodEntry).filter(
            FoodEntry.user_id == user_id
        ).order_by(FoodEntry.date.desc(), FoodEntry.id.desc()).limit(limit).all()