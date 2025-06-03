from database import engine
from sqlalchemy import text  

print("=== DATABASE CONNECTION TEST ===")

try:
    with engine.connect() as conn:
        print("✓ Connection successful")
        
        
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result]
        print(f"Tables found: {tables}")
        
except Exception as e:
    print(f"✗ Error: {e}")