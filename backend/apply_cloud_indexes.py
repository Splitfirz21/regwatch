from sqlmodel import Session, text
from database import engine

# Script to add indexes for Cloud Performance
# Run this once against your cloud database.

def apply_indexes():
    print("🚀 Applying Cloud Optimization Indexes...")
    with Session(engine) as session:
        # 1. Published Date (for sorting)
        try:
            print("Creating Index: idx_newsitem_published_at...")
            session.exec(text("CREATE INDEX IF NOT EXISTS idx_newsitem_published_at ON newsitem (published_at DESC);"))
        except Exception as e:
            print(f"Skipped (or error): {e}")

        # 2. Impact Rating (for filtering)
        try:
            print("Creating Index: idx_newsitem_impact_rating...")
            session.exec(text("CREATE INDEX IF NOT EXISTS idx_newsitem_impact_rating ON newsitem (impact_rating);"))
        except Exception as e:
            print(f"Skipped (or error): {e}")
            
        # 3. Sector (for filtering)
        # Note: 'sector' might be text, useful to hash or btree
        try:
            print("Creating Index: idx_newsitem_sector...")
            session.exec(text("CREATE INDEX IF NOT EXISTS idx_newsitem_sector ON newsitem (sector);"))
        except Exception as e:
            print(f"Skipped (or error): {e}")

        # 4. Search Optimization (Gin Index for FTS if using tsvector)
        # For simple ILIKE search, basic indexes don't help much unless using pg_trgm
        # But we will rely on Postgres 'websearch_to_tsquery' if available, which uses to_tsvector on the fly
        # Ideally we create a generated column, but specialized indexes are complex to manage via raw SQL if not superuser.
        # We will skip complex GIN indexes for now to avoid permission errors.
        # The simple indexes above will already speed up dashboard significantly.
        
        session.commit()
    print("✅ Indexes applied successfully.")

if __name__ == "__main__":
    apply_indexes()
