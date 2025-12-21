from sqlmodel import Session, select
from database import engine
from models import NewsItem
import os

# To target Cloud DB, set DATABASE_URL environment variable before running.
# Example: export DATABASE_URL="postgresql://..."

def cleanup():
    print("🧹 Cleaning up 'Related Sources' data...")
    with Session(engine) as session:
        # Find items with related sources
        # We check for NOT None. Empty list is fine but better to just wipe everything to None or []
        # JSON column filtering depends on DB (SQLite vs Postgres). 
        # Safest way: iterate and update.
        
        items = session.exec(select(NewsItem)).all()
        count = 0
        
        for item in items:
            if item.related_sources: # If list is not empty or None
                item.related_sources = None # Wipe it
                session.add(item)
                count += 1
        
        session.commit()
        print(f"✅ Cleaned {count} articles. 'Also seen on' data is now gone.")

if __name__ == "__main__":
    cleanup()
