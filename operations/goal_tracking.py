from datetime import date
from typing import Dict, Optional
from sqlalchemy.orm import Session
from models.goal import Goal

class GoalOps:
    def __init__(self, db: Session):
        self.db = db
    
    def set_goals(self, user_id: int, daily: int, weekly: int) -> Goal:
        """Create or update nutrition goals
        
        Args:
            user_id: ID of the user
            daily: Daily calorie goal
            weekly: Weekly calorie goal
            
        Returns:
            The created or updated Goal object
        """
        goal = self.db.query(Goal).filter(Goal.user_id == user_id).first()
        if not goal:
            goal = Goal(user_id=user_id)
            self.db.add(goal)
        
        goal.daily_calories = daily
        goal.weekly_calories = weekly
        
        
        
        self.db.commit()
        return goal
    
    def get_goals(self, user_id: int) -> Optional[Goal]:
        """Get user's goals
        
        Args:
            user_id: ID of the user
            
        Returns:
            Goal object if found, None otherwise
        """
        return self.db.query(Goal).filter(Goal.user_id == user_id).first()
    
    def get_progress(self, user_id: int, target_date: date) -> Dict:
        """Calculate daily progress vs goals
        
        Args:
            user_id: ID of the user
            target_date: Date to calculate progress for
            
        Returns:
            Dictionary containing:
                - date: The target date
                - total_calories: Sum of calories consumed
                - daily_goal: User's daily goal (None if not set)
                - remaining: Remaining calories to meet goal (None if goal not set)
                - progress_percentage: Percentage of goal achieved (0-100)
        """
        from operations.food_log import FoodLogOps
        food_ops = FoodLogOps(self.db)
        
        goals = self.get_goals(user_id)
        entries = food_ops.get_daily_logs(user_id, target_date)
        
        total_calories = sum(e.calories for e in entries) if entries else 0
        
        result = {
            "date": target_date,
            "total_calories": total_calories,
            "daily_goal": goals.daily_calories if goals else None,
            "remaining": None,
            "progress_percentage": None
        }
        
        if goals and goals.daily_calories:
            result["remaining"] = max(0, goals.daily_calories - total_calories)
            if goals.daily_calories > 0:
                result["progress_percentage"] = min(
                    100, 
                    round((total_calories / goals.daily_calories) * 100, 2)
                )
        
        return result
    
    def get_weekly_progress(self, user_id: int, start_date: date) -> Dict:
        """Calculate weekly progress vs goals
        
        Args:
            user_id: ID of the user
            start_date: Start date of the week (typically Monday)
            
        Returns:
            Dictionary containing weekly progress information
        """
        from operations.food_log import FoodLogOps
        food_ops = FoodLogOps(self.db)
        
        goals = self.get_goals(user_id)
        end_date = date.fromordinal(start_date.toordinal() + 6)
        
        entries = food_ops.get_logs_in_range(user_id, start_date, end_date)
        total_calories = sum(e.calories for e in entries) if entries else 0
        
        result = {
            "start_date": start_date,
            "end_date": end_date,
            "total_calories": total_calories,
            "weekly_goal": goals.weekly_calories if goals else None,
            "remaining": None,
            "progress_percentage": None
        }
        
        if goals and goals.weekly_calories:
            result["remaining"] = max(0, goals.weekly_calories - total_calories)
            if goals.weekly_calories > 0:
                result["progress_percentage"] = min(
                    100, 
                    round((total_calories / goals.weekly_calories) * 100, 2)
                )
        
        return result