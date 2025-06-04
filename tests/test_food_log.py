from operations.food_log import FoodLogOps
from models.food_entry import FoodEntry
from datetime import date

def test_log_meal(db_session):
    ops = FoodLogOps(db_session)
    entry = ops.log_meal(1, "Apple", 95)
    
    assert entry.id is not None
    assert entry.food_name == "Apple"
    assert entry.calories == 95
    assert entry.date == date.today()