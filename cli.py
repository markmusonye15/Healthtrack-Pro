import typer
from logging_config import setup_logging
import logging
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models.user import User
from models.food_entry import FoodEntry
from models.goal import Goal
from operations.food_log import FoodLogOps
from operations.goal_tracking import GoalOps
from operations.meal_planning import MealPlanner

# Initialize app and logging
app = typer.Typer(rich_markup_mode="markdown")
setup_logging()
logger = logging.getLogger("healthtrack.cli")

# Database session helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def get_user_by_name(db: Session, name: str) -> User:
    user = db.query(User).filter(User.name == name).first()
    if not user:
        raise typer.BadParameter(f"User '{name}' not found")
    return user

# User Management Commands
@app.command()
def user_create(name: str):
    """Create a new user"""
    db = SessionLocal()
    try:
        if db.query(User).filter(User.name == name).first():
            typer.echo(f"❌ User '{name}' already exists")
            return
            
        user = User(name=name)
        db.add(user)
        db.commit()
        typer.echo(f"✅ Created user: {name} (ID: {user.id})")
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()

@app.command()
def user_list():
    """List all users"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            typer.echo("No users found")
            return
            
        typer.echo("\nUsers:")
        for user in users:
            typer.echo(f"- {user.name} (ID: {user.id})")
    finally:
        db.close()

# Food Entry Commands
@app.command()
def entry_add(
    user: str = typer.Option(..., "--user"),
    food: str = typer.Option(..., "--food"),
    calories: int = typer.Option(..., "--calories"),
    date_str: str = typer.Option(None, "--date")  # Changed parameter name
):
    """Add a food entry"""
    db = SessionLocal()
    try:
        user_obj = get_user_by_name(db, user)
        
        
        if date_str is None:
            entry_date = date.today()
        else:
            try:
                entry_date = date.fromisoformat(date_str)
            except ValueError:
                raise typer.BadParameter("Date must be in YYYY-MM-DD format")
        
        entry = FoodEntry(
            user_id=user_obj.id,
            food_name=food,
            calories=calories,
            date=entry_date
        )
        db.add(entry)
        db.commit()
        typer.echo(f"✅ Added entry: {food} ({calories} cal) on {entry_date}")
    except typer.BadParameter as e:
        typer.echo(f"❌ {str(e)}", err=True)
        db.rollback()
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()

@app.command()
def entry_list(
    user: str = typer.Option(None, "--user"),
    date: str = typer.Option(None, "--date")
):
    """List food entries"""
    db = SessionLocal()
    try:
        query = db.query(FoodEntry)
        
        if user:
            user_obj = get_user_by_name(db, user)
            query = query.filter(FoodEntry.user_id == user_obj.id)
            
        if date:
            date_obj = date.fromisoformat(date)
            query = query.filter(FoodEntry.date == date_obj)
            
        entries = query.all()
        
        if not entries:
            typer.echo("No entries found")
            return
            
        typer.echo("\nFood Entries:")
        for entry in entries:
            user_name = db.query(User).get(entry.user_id).name
            typer.echo(f"- ID: {entry.id} | User: {user_name} | {entry.date}")
            typer.echo(f"  {entry.food_name}: {entry.calories} cal")
    finally:
        db.close()

@app.command()
def entry_update(
    id: int = typer.Option(..., "--id"),
    food: str = typer.Option(None, "--food"),
    calories: int = typer.Option(None, "--calories"),
    date: str = typer.Option(None, "--date")
):
    """Update a food entry"""
    db = SessionLocal()
    try:
        entry = db.query(FoodEntry).filter(FoodEntry.id == id).first()
        if not entry:
            typer.echo(f"❌ Entry ID {id} not found")
            return
            
        if food:
            entry.food_name = food
        if calories:
            entry.calories = calories
        if date:
            entry.date = date.fromisoformat(date)
            
        db.commit()
        typer.echo(f"✅ Updated entry ID {id}")
    except ValueError:
        typer.echo("❌ Invalid date format. Use YYYY-MM-DD", err=True)
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()

@app.command()
def entry_delete(id: int = typer.Option(..., "--id")):
    """Delete a food entry"""
    db = SessionLocal()
    try:
        entry = db.query(FoodEntry).filter(FoodEntry.id == id).first()
        if not entry:
            typer.echo(f"❌ Entry ID {id} not found")
            return
            
        db.delete(entry)
        db.commit()
        typer.echo(f"✅ Deleted entry ID {id}")
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()

# Goal Commands
@app.command()
def goal_set(
    user: str = typer.Option(..., "--user"),
    daily: int = typer.Option(..., "--daily"),
    weekly: int = typer.Option(..., "--weekly")
):
    """Set user goals"""
    db = SessionLocal()
    try:
        user_obj = get_user_by_name(db, user)
        goal_ops = GoalOps(db)
        goal = goal_ops.set_goals(user_obj.id, daily, weekly)
        typer.echo(f"⚡ Goals set for {user}:")
        typer.echo(f"• Daily: {daily} calories")
        typer.echo(f"• Weekly: {weekly} calories")
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()

@app.command()
def goal_list(user: str = typer.Option(..., "--user")):
    """List user goals"""
    db = SessionLocal()
    try:
        user_obj = get_user_by_name(db, user)
        goal = db.query(Goal).filter(Goal.user_id == user_obj.id).first()
        
        if not goal:
            typer.echo(f"No goals set for {user}")
            return
            
        typer.echo(f"\nGoals for {user}:")
        typer.echo(f"• Daily: {goal.daily_calories} calories")
        typer.echo(f"• Weekly: {goal.weekly_calories} calories")
    finally:
        db.close()

# Reporting Commands
@app.command()
def report_daily(
    user: str = typer.Option(..., "--user"),
    date_str: str = typer.Option(None, "--date")  # Changed from 'date' to 'date_str'
):
    """Generate daily report"""
    db = SessionLocal()
    try:
        user_obj = get_user_by_name(db, user)
        
        # Handle date parsing
        if date_str is None:
            report_date = date.today()
        else:
            try:
                report_date = date.fromisoformat(date_str)
            except ValueError:
                raise typer.BadParameter("Date must be in YYYY-MM-DD format")
        
        entries = db.query(FoodEntry).filter(
            FoodEntry.user_id == user_obj.id,
            FoodEntry.date == report_date
        ).all()
        
        goal = db.query(Goal).filter(Goal.user_id == user_obj.id).first()
        
        typer.echo(f"\n📊 Daily Report for {user} - {report_date}")
        typer.echo("="*40)
        
        if not entries:
            typer.echo("No entries for this date")
            return
            
        total_calories = sum(e.calories for e in entries)
        
        typer.echo("\nFood Entries:")
        for entry in entries:
            typer.echo(f"- {entry.food_name}: {entry.calories} cal")
            
        typer.echo(f"\nTotal Calories: {total_calories}")
        
        if goal:
            remaining = goal.daily_calories - total_calories
            percentage = min(100, (total_calories / goal.daily_calories) * 100)
            
            typer.echo(f"🎯 Goal: {goal.daily_calories} ({percentage:.1f}%)")
            typer.echo(f"⏳ Remaining: {remaining} calories")
            
            # Progress bar
            bar_length = 30
            filled = int(bar_length * percentage / 100)
            typer.secho(
                "[" + "=" * filled + " " * (bar_length - filled) + "]",
                fg="green" if percentage < 90 else "yellow" if percentage < 110 else "red"
            )
            
    except typer.BadParameter as e:
        typer.echo(f"❌ {str(e)}", err=True)
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {str(e)}", err=True)
    finally:
        db.close()

# Meal Planning Commands
@app.command()
def plan_meal_generate(
    user: str = typer.Option(..., "--user"),
    weeks: int = typer.Option(1, "--weeks")
):
    """Generate meal plan"""
    db = SessionLocal()
    try:
        user_obj = get_user_by_name(db, user)
        planner = MealPlanner(db)
        
        for week in range(weeks):
            start_date = date.today() + timedelta(weeks=week)
            plan = planner.generate_weekly_plan(user_obj.id, start_date)
            
            typer.echo(f"\n🍽 Meal Plan for Week {week+1} ({start_date} to {start_date + timedelta(days=6)})")
            for day, meals in plan.items():
                typer.echo(f"\n{day}:")
                for meal in meals:
                    typer.echo(f"- {meal['name']}: {meal['calories']} cal")
                    
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()

@app.command()
def plan_meal_update(
    id: int = typer.Option(..., "--id"),
    meal: str = typer.Option(None, "--meal"),
    calories: int = typer.Option(None, "--calories")
):
    """Update meal plan entry"""
    db = SessionLocal()
    try:
        # Implement your meal plan update logic here
        typer.echo(f"✅ Updated meal plan entry ID {id}")
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    app()