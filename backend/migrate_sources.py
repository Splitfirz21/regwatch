
from sqlmodel import Session, text
from database import engine

def migrate_db():
    print("Migrating Database: Adding related_sources column...")
    with Session(engine) as session:
        try:
            # Check if column exists first? 
            # SQLite doesn't have IF NOT EXISTS for columns in older versions, but let's try just adding.
            # We map JSON to custom type, probably stored as JSON or TEXT.
            # In SQLite, JSON is just a validity check on TEXT.
            session.exec(text("ALTER TABLE newsitem ADD COLUMN related_sources JSON;"))
            session.commit()
            print("Migration Successful.")
        except Exception as e:
            print(f"Migration might have failed (or column exists): {e}")

if __name__ == "__main__":
    migrate_db()
