import typer
from datetime import date
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models.user import User
from models.food_entry import FoodEntry
from models.goal import Goal

app = typer.Typer()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.command()
def create_user(name: str):
    """Create a new user"""
    db = SessionLocal()
    try:
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
def add_food(
    user_name: str,
    food: str,
    calories: int,
    date_str = typer.Option(None, "--date", help="YYYY-MM-DD")
):
    """Log a food entry"""
    db = SessionLocal()
    try:
        print(f"DEBUG: Adding food for{user_name}")
        # Get user
        user = db.query(User).filter(User.name == user_name).first()
        if not user:
            raise typer.BadParameter(f"User '{user_name}' not found")
        
        # Parse date
        entry_date = date.today() if not date_str else date.fromisoformat(date_str)
        
        # Create entry
        entry = FoodEntry(
            food_name=food,
            calories=calories,
            date=entry_date,
            user_id=user.id
        )
        db.add(entry)
        db.commit()
        print(f"DEBUG: Entry committed with ID {entry.id}")
        typer.echo(f"✅ Logged {food} ({calories} cal) for {user_name} on {entry_date}")
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()

@app.command()
def set_goals(
    user_name: str,
    daily: int = typer.Option(..., "--daily", help="Daily calorie goal"),
    weekly: int = typer.Option(..., "--weekly", help="Weekly calorie goal"),
    protein: float = typer.Option(None, "--protein", help="Daily protein goal in grams"),
    carbs: float = typer.Option(None, "--carbs", help="Daily carb goal in grams"),
    fats: float = typer.Option(None, "--fats", help="Daily fat goal in grams")
):
    """Set or update nutrition goals"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.name == user_name).first()
        if not user:
            raise typer.BadParameter(f"User '{user_name}' not found")
        
        goal = db.query(Goal).filter(Goal.user_id == user.id).first()
        if not goal:
            goal = Goal(user_id=user.id)
            db.add(goal)
        
        goal.daily_calories = daily
        goal.weekly_calories = weekly
        if protein is not None:
            goal.protein_goal = protein
        if carbs is not None:
            goal.carb_goal = carbs
        if fats is not None:
            goal.fat_goal = fats
        
        db.commit()
        typer.echo(f"⚡ Goals set for {user_name}:")
        typer.echo(f"• Calories: {daily} daily / {weekly} weekly")
        if protein:
            typer.echo(f"• Protein: {protein}g")
        if carbs:
            typer.echo(f"• Carbs: {carbs}g")
        if fats:
            typer.echo(f"• Fats: {fats}g")
            
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        db.close()
@app.command()
def daily_report(user_name: str):
    """Show today's nutrition summary"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.name == user_name).first()
        if not user:
            raise typer.BadParameter(f"User '{user_name}' not found")
        
        today = date.today()
        entries = db.query(FoodEntry).filter(
            FoodEntry.user_id == user.id,
            FoodEntry.date == today
        ).all()
        
        if not entries:
            typer.echo(f"No entries found for {user_name} today")
            return
            
        total_cal = sum(e.calories for e in entries)
        goal = db.query(Goal).filter(Goal.user_id == user.id).first()
        
        typer.echo(f"\n📊 Daily Report for {user_name} ({today})")
        typer.echo(f"🍽️ Total Calories: {total_cal}/{goal.daily_calories if goal else 'N/A'}")
        
    finally:
        db.close()
        

    
        
