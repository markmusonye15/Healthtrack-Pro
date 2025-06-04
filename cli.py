import typer
from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models.user import User
from models.food_entry import FoodEntry
from models.goal import Goal
from operations.food_log import FoodLogOps
from operations.goal_tracking import GoalOps
from operations.meal_planning import MealPlanner 

app = typer.Typer(rich_markup_mode="markdown")

# Database dependency 
def get_db() -> Session:
    """Yields a database session that auto-closes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_by_name(db: Session, name: str) -> User:
    """Helper to get user with proper error handling"""
    user = db.query(User).filter(User.name == name).first()
    if not user:
        raise typer.BadParameter(f"User '{name}' not found")
    return user

@app.command()
def create_user(name: str):
    """Create a new user with the specified name"""
    db = SessionLocal()
    try:
        if db.query(User).filter(User.name == name).first():
            raise typer.BadParameter(f"User '{name}' already exists")
            
        user = User(name=name)
        db.add(user)
        db.commit()
        typer.secho(f"✅ Created user: {name} (ID: {user.id})", fg="green")
    except Exception as e:
        db.rollback()
        typer.secho(f"❌ Error: {str(e)}", fg="red", err=True)
    finally:
        db.close()

@app.command()
def add_food(
    user_name: str,
    food: str,
    calories: int,
    date_str: str = typer.Option(None, "--date", help="YYYY-MM-DD")
):
    """Log a food entry """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.name == user_name).first()
        if not user:
            raise typer.BadParameter(f"User '{user_name}' not found")
        
        entry_date = date.today() if not date_str else date.fromisoformat(date_str)
        
        food_ops = FoodLogOps(db)
        entry = food_ops.log_meal(
            user_id=user.id,
            food_name=food,
            calories=calories,
            meal_date=entry_date
        )
        
        typer.echo(f"✅ Logged {food} ({calories} cal) for {user_name} on {entry_date}")
    except ValueError:
        typer.echo("❌ Invalid date format. Use YYYY-MM-DD", err=True)
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()
        
      

@app.command()

def set_goals(
    user_name: str,
    daily: int = typer.Option(..., "--daily", help="Daily calorie goal"),
    weekly: int = typer.Option(..., "--weekly", help="Weekly calorie goal")
):
    """Set or update basic nutrition goals"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.name == user_name).first()
        if not user:
            raise typer.BadParameter(f"User '{user_name}' not found")
        
        goal_ops = GoalOps(db)
        goal = goal_ops.set_goals(
            user_id=user.id,
            daily=daily,
            weekly=weekly
        )
        
        typer.echo(f"⚡ Goals set for {user_name}:")
        typer.echo(f"• Calories: {daily} daily / {weekly} weekly")
            
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()

@app.command()
def daily_report(user_name: str):
    """Show today's nutrition summary (simplified)"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.name == user_name).first()
        if not user:
            raise typer.BadParameter(f"User '{user_name}' not found")
        
        today = date.today()
        food_ops = FoodLogOps(db)
        entries = food_ops.get_daily_logs(user.id, today)
        
        if not entries:
            typer.echo(f"No entries found for {user_name} today")
            return
            
        total_cal = sum(e.calories for e in entries)
        goal_ops = GoalOps(db)
        goal = goal_ops.get_goals(user.id)
        
        typer.echo(f"\n📊 Daily Report for {user_name} ({today})")
        typer.echo(f"🍽️ Total Calories: {total_cal}")
        
        if goal and goal.daily_calories:
            remaining = max(0, goal.daily_calories - total_cal)
            percentage = min(100, (total_cal / goal.daily_calories) * 100)
            
            typer.echo(f"🎯 Goal: {goal.daily_calories} ({percentage:.1f}%)")
            typer.echo(f"⏳ Remaining: {remaining} cal")
            
            # Progress bar visualization
            bar_length = 30
            filled = int(bar_length * percentage / 100)
            typer.secho(
                "[" + "=" * filled + " " * (bar_length - filled) + "]",
                fg="green" if percentage < 90 else "yellow" if percentage < 110 else "red"
            )
    finally:
        db.close()

@app.command()
def weekly_report(
    user_name: str,
    week_start: Optional[str] = typer.Option(None, "--week-start", "-w", help="Start date in YYYY-MM-DD format")
):
    """Show weekly nutrition overview"""
    db = SessionLocal()
    try:
        user = get_user_by_name(db, user_name)
        start_date = (date.today() - timedelta(days=date.today().weekday())) if not week_start else date.fromisoformat(week_start)
        end_date = start_date + timedelta(days=6)
        
        planner = MealPlanner(db)
        week_data = planner.get_weekly_nutrition(user.id, start_date)
        goal = GoalOps(db).get_goals(user.id)
        
        # Display header
        typer.secho(f"\n📅 Weekly Report: {start_date} to {end_date}", fg="blue", bold=True)
        typer.secho("="*60, fg="blue")
        
        # Daily breakdown
        for day, data in week_data.items():
            day_name = day.strftime("%A")
            goal_met = "✅" if goal and goal.daily_calories and data['total_calories'] <= goal.daily_calories else "⚠️"
            
            typer.secho(f"\n{day_name} ({day}):", fg="yellow")
            typer.echo(f"{goal_met} Calories: {data['total_calories']}/{goal.daily_calories if goal else 'N/A'}")
            typer.echo(f"🍽 Meals: {', '.join(data['meal_types'])}")
            
    finally:
        db.close()

@app.command()
def weekly_report(user_name: str):
    """Show weekly nutrition overview (simplified without meal types)"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.name == user_name).first()
        if not user:
            raise typer.BadParameter(f"User '{user_name}' not found")
        
        start_date = date.today() - timedelta(days=date.today().weekday())
        end_date = start_date + timedelta(days=6)
        
        # Get food entries
        entries = db.query(FoodEntry).filter(
            FoodEntry.user_id == user.id,
            FoodEntry.date >= start_date,
            FoodEntry.date <= end_date
        ).all()
        
        # Get goals
        goal = db.query(Goal).filter(Goal.user_id == user.id).first()
        
        # Display report
        typer.echo(f"\n📅 Weekly Report: {start_date} to {end_date}")
        typer.echo("="*40)
        
        current_date = start_date
        while current_date <= end_date:
            daily_entries = [e for e in entries if e.date == current_date]
            total_cal = sum(e.calories for e in daily_entries)
            
            typer.echo(f"\n{current_date.strftime('%A')} ({current_date}):")
            typer.echo(f"🍽️ Total Calories: {total_cal}")
            
            if goal and goal.daily_calories:
                status = "✅" if total_cal <= goal.daily_calories else "⚠️"
                typer.echo(f"{status} Daily Goal: {goal.daily_calories}")
            
            current_date += timedelta(days=1)
            
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    app()