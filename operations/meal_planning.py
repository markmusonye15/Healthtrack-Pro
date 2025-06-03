from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Optional, Dict
from models.food_entry import FoodEntry
from collections import defaultdict

class MealPlanner:
    def __init__(self, db: Session):
        self.db = db
    
    def log_meal(
        self,
        user_id: int,
        food: str,
        calories: int,
        meal_type: str,
        meal_date: date = None,
        notes: str = None
    ) -> FoodEntry:
        """Log a meal with additional context for better planning
        
        Args:
            user_id: ID of the user
            food: Name of food item
            calories: Calorie count (must be positive)
            meal_type: Type of meal (breakfast/lunch/dinner/snack)
            meal_date: Date of meal (defaults to today)
            notes: Optional notes about the meal
            
        Returns:
            The created FoodEntry object
            
        Raises:
            ValueError: If calories are negative or meal_type is invalid
        """
        if calories < 0:
            raise ValueError("Calories cannot be negative")
            
        valid_meal_types = ["breakfast", "lunch", "dinner", "snack"]
        if meal_type.lower() not in valid_meal_types:
            raise ValueError(f"Invalid meal type. Must be one of: {', '.join(valid_meal_types)}")

        entry = FoodEntry(
            user_id=user_id,
            food_name=food,
            calories=calories,
            meal_type=meal_type.lower(),
            date=meal_date or date.today(),
            notes=notes
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def get_daily_logs(
        self,
        user_id: int,
        target_date: date,
        group_by_meal_type: bool = False
    ) -> List[FoodEntry] | Dict[str, List[FoodEntry]]:
        """Get food entries for a specific day
        
        Args:
            user_id: ID of the user
            target_date: Date to retrieve logs for
            group_by_meal_type: If True, returns dict grouped by meal type
            
        Returns:
            List of entries or dict of lists grouped by meal type
        """
        entries = self.db.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            FoodEntry.date == target_date
        ).order_by(FoodEntry.meal_type, FoodEntry.id).all()
        
        if group_by_meal_type:
            grouped = defaultdict(list)
            for entry in entries:
                grouped[entry.meal_type].append(entry)
            return dict(grouped)
        return entries
    
    def get_weekly_nutrition(
        self,
        user_id: int,
        start_date: date
    ) -> Dict[date, Dict[str, int]]:
        """Get weekly nutrition summary
        
        Args:
            user_id: ID of the user
            start_date: Start date of the week (typically Monday)
            
        Returns:
            Dictionary with date keys and nutrition summaries
        """
        end_date = start_date + timedelta(days=6)
        entries = self.db.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            FoodEntry.date >= start_date,
            FoodEntry.date <= end_date
        ).all()
        
        weekly_data = {}
        current_date = start_date
        while current_date <= end_date:
            daily_entries = [e for e in entries if e.date == current_date]
            weekly_data[current_date] = {
                'total_calories': sum(e.calories for e in daily_entries),
                'meal_count': len(daily_entries),
                'meal_types': {e.meal_type for e in daily_entries}
            }
            current_date += timedelta(days=1)
            
        return weekly_data
    
    def suggest_meal_plan(
        self,
        user_id: int,
        target_date: date,
        calorie_target: int,
        existing_calories: int = 0
    ) -> Dict[str, Dict]:
        """Suggest a meal plan based on remaining calories
        
        Args:
            user_id: ID of the user
            target_date: Date for the plan
            calorie_target: Daily calorie goal
            existing_calories: Calories already consumed
            
        Returns:
            Dictionary with suggested meals and nutrition info
        """
        remaining_calories = calorie_target - existing_calories
        
        
        suggestions = {
            'breakfast': {
                'suggestion': "Greek yogurt with berries and granola",
                'estimated_calories': 300 if remaining_calories >= 1600 else 200
            },
            'lunch': {
                'suggestion': "Grilled chicken salad with olive oil dressing",
                'estimated_calories': 450 if remaining_calories >= 1200 else 350
            },
            'dinner': {
                'suggestion': "Salmon with quinoa and steamed vegetables",
                'estimated_calories': 550 if remaining_calories >= 700 else 400
            },
            'snack': {
                'suggestion': "Handful of almonds" if remaining_calories > 200 else "Apple slices",
                'estimated_calories': 150
            }
        }
        
        # Adjust based on remaining calories
        total_suggested = sum(m['estimated_calories'] for m in suggestions.values())
        if total_suggested > remaining_calories:
            for meal in suggestions.values():
                meal['estimated_calories'] = int(meal['estimated_calories'] * 0.8)
                
        return suggestions
    
    def get_meal_history(
        self,
        user_id: int,
        meal_type: str,
        limit: int = 5
    ) -> List[FoodEntry]:
        """Get recent history of a specific meal type
        
        Args:
            user_id: ID of the user
            meal_type: Type of meal to search for
            limit: Number of results to return
            
        Returns:
            List of recent meal entries of the specified type
        """
        return self.db.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            FoodEntry.meal_type == meal_type.lower()
        ).order_by(FoodEntry.date.desc(), FoodEntry.id.desc()).limit(limit).all()