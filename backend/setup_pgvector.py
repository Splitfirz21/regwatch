from sqlmodel import Session, text
from database import engine

def setup_vector_db():
    print("🚀 Setting up PGVector on Database...")
    with Session(engine) as session:
        try:
            # 1. Enable Extension
            print("1. Enabling 'vector' extension...")
            session.exec(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            session.commit()
            print("   ✅ Extension enabled.")
        except Exception as e:
            print(f"   ⚠️ Error enabling extension (might already exist or need permissions): {e}")
            
        try:
            # 2. Add Column
            # We use raw SQL because SQLModel migration is manual in this setup
            print("2. Adding 'embedding' column to newsitem table...")
            # Check if column exists first to avoid error? Or just use safe alter?
            # Postgres doesn't have "ADD COLUMN IF NOT EXISTS" in all versions easily without DO block.
            # Simpler: Try add, catch error if exists.
            
            session.exec(text("ALTER TABLE newsitem ADD COLUMN IF NOT EXISTS embedding vector(768);"))
            session.commit()
            print("   ✅ Column added.")
        except Exception as e:
            print(f"   ⚠️ Error adding column (might already exist): {e}")
            
    print("✨ Database upgrade complete.")

if __name__ == "__main__":
    setup_vector_db()
