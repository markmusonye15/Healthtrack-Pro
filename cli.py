import typer
from logging_config import setup_logging
import logging
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
import sys

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

# =============================================
# Interactive UI Implementation
# =============================================

def display_menu():
    """Display the main menu"""
    print("\n" + "="*50)
    print("HealthTrack Pro - Main Menu")
    print("="*50)
    print("1. User Management")
    print("2. Food Entry Management")
    print("3. Goal Management")
    print("4. Reports")
    print("5. Meal Planning")
    print("0. Exit")
    print("="*50)

def user_management_menu():
    """Display user management menu"""
    print("\n" + "="*50)
    print("User Management")
    print("="*50)
    print("1. Create User")
    print("2. List Users")
    print("0. Back to Main Menu")
    print("="*50)

def food_entry_menu():
    """Display food entry menu"""
    print("\n" + "="*50)
    print("Food Entry Management")
    print("="*50)
    print("1. Add Food Entry")
    print("2. List Food Entries")
    print("3. Update Food Entry")
    print("4. Delete Food Entry")
    print("0. Back to Main Menu")
    print("="*50)

def goal_management_menu():
    """Display goal management menu"""
    print("\n" + "="*50)
    print("Goal Management")
    print("="*50)
    print("1. Set Goals")
    print("2. List Goals")
    print("0. Back to Main Menu")
    print("="*50)

def reports_menu():
    """Display reports menu"""
    print("\n" + "="*50)
    print("Reports")
    print("="*50)
    print("1. Daily Report")
    print("0. Back to Main Menu")
    print("="*50)

def meal_planning_menu():
    """Display meal planning menu"""
    print("\n" + "="*50)
    print("Meal Planning")
    print("="*50)
    print("1. Generate Meal Plan")
    print("2. Update Meal Plan Entry")
    print("0. Back to Main Menu")
    print("="*50)

def get_input(prompt: str, required: bool = True) -> str:
    """Helper function to get user input"""
    while True:
        user_input = input(prompt).strip()
        if not user_input and required:
            print("This field is required. Please try again.")
            continue
        return user_input

def get_date_input(prompt: str) -> Optional[str]:
    """Helper function to get date input"""
    while True:
        date_str = input(prompt + " (YYYY-MM-DD, leave blank for today): ").strip()
        if not date_str:
            return None
        try:
            date.fromisoformat(date_str)
            return date_str
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

def run_cli():
    """Main function to run the CLI interface"""
    while True:
        display_menu()
        choice = get_input("Enter your choice: ")
        
        if choice == "0":
            print("Exiting HealthTrack CLI. Goodbye!")
            sys.exit(0)
            
        elif choice == "1":  # User Management
            while True:
                user_management_menu()
                sub_choice = get_input("Enter your choice: ")
                
                if sub_choice == "0":
                    break
                elif sub_choice == "1":  # Create User
                    name = get_input("Enter user name: ")
                    user_create(name=name)
                elif sub_choice == "2":  # List Users
                    user_list()
                else:
                    print("Invalid choice. Please try again.")
                    
        elif choice == "2":  # Food Entry Management
            while True:
                food_entry_menu()
                sub_choice = get_input("Enter your choice: ")
                
                if sub_choice == "0":
                    break
                elif sub_choice == "1":  # Add Food Entry
                    user = get_input("Enter user name: ")
                    food = get_input("Enter food name: ")
                    calories = get_input("Enter calories: ")
                    date_str = get_date_input("Enter date: ")
                    
                    try:
                        calories_int = int(calories)
                        entry_add(user=user, food=food, calories=calories_int, date_str=date_str)
                    except ValueError:
                        print("Calories must be a number. Please try again.")
                        
                elif sub_choice == "2":  # List Food Entries
                    user = get_input("Enter user name (leave blank for all users): ", required=False)
                    date_str = get_date_input("Enter date: ")
                    entry_list(user=user if user else None, date=date_str)
                    
                elif sub_choice == "3":  # Update Food Entry
                    entry_id = get_input("Enter entry ID to update: ")
                    food = get_input("Enter new food name (leave blank to keep current): ", required=False)
                    calories = get_input("Enter new calories (leave blank to keep current): ", required=False)
                    date_str = get_date_input("Enter new date: ")
                    
                    try:
                        entry_id_int = int(entry_id)
                        calories_int = int(calories) if calories else None
                        entry_update(
                            id=entry_id_int,
                            food=food if food else None,
                            calories=calories_int,
                            date=date_str
                        )
                    except ValueError:
                        print("ID and calories must be numbers. Please try again.")
                        
                elif sub_choice == "4":  # Delete Food Entry
                    entry_id = get_input("Enter entry ID to delete: ")
                    try:
                        entry_id_int = int(entry_id)
                        entry_delete(id=entry_id_int)
                    except ValueError:
                        print("ID must be a number. Please try again.")
                else:
                    print("Invalid choice. Please try again.")
                    
        elif choice == "3":  # Goal Management
            while True:
                goal_management_menu()
                sub_choice = get_input("Enter your choice: ")
                
                if sub_choice == "0":
                    break
                elif sub_choice == "1":  # Set Goals
                    user = get_input("Enter user name: ")
                    daily = get_input("Enter daily calorie goal: ")
                    weekly = get_input("Enter weekly calorie goal: ")
                    
                    try:
                        daily_int = int(daily)
                        weekly_int = int(weekly)
                        goal_set(user=user, daily=daily_int, weekly=weekly_int)
                    except ValueError:
                        print("Goals must be numbers. Please try again.")
                        
                elif sub_choice == "2":  # List Goals
                    user = get_input("Enter user name: ")
                    goal_list(user=user)
                else:
                    print("Invalid choice. Please try again.")
                    
        elif choice == "4":  # Reports
            while True:
                reports_menu()
                sub_choice = get_input("Enter your choice: ")
                
                if sub_choice == "0":
                    break
                elif sub_choice == "1":  # Daily Report
                    user = get_input("Enter user name: ")
                    date_str = get_date_input("Enter date: ")
                    report_daily(user=user, date_str=date_str)
                else:
                    print("Invalid choice. Please try again.")
                    
        elif choice == "5":  # Meal Planning
            while True:
                meal_planning_menu()
                sub_choice = get_input("Enter your choice: ")
                
                if sub_choice == "0":
                    break
                elif sub_choice == "1":  # Generate Meal Plan
                    user = get_input("Enter user name: ")
                    weeks = get_input("Enter number of weeks to plan (default 1): ", required=False)
                    
                    try:
                        weeks_int = int(weeks) if weeks else 1
                        plan_meal_generate(user=user, weeks=weeks_int)
                    except ValueError:
                        print("Weeks must be a number. Please try again.")
                        
                elif sub_choice == "2":  # Update Meal Plan Entry
                    entry_id = get_input("Enter meal plan entry ID: ")
                    meal = get_input("Enter new meal name (leave blank to keep current): ", required=False)
                    calories = get_input("Enter new calories (leave blank to keep current): ", required=False)
                    
                    try:
                        entry_id_int = int(entry_id)
                        calories_int = int(calories) if calories else None
                        plan_meal_update(
                            id=entry_id_int,
                            meal=meal if meal else None,
                            calories=calories_int
                        )
                    except ValueError:
                        print("ID and calories must be numbers. Please try again.")
                else:
                    print("Invalid choice. Please try again.")
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    init_db()
    
    if len(sys.argv) == 1:
        run_cli()  # Launch the interactive UI
    else:
        app()  