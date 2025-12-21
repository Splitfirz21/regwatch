
import os
from sqlmodel import SQLModel, create_engine, Session, select
from models import NewsItem, UserInterest
from sqlalchemy import create_engine as sa_create_engine

# 1. Local Connection (Source)
LOCAL_DB_URL = "sqlite:///database.db"
local_engine = create_engine(LOCAL_DB_URL)

def migrate_data():
    print("🚀 Starting Migration: Local SQLite -> Cloud Postgres")
    
    # Get Cloud URL
    cloud_url = input("Enter your Neon/Render DATABASE_URL (postgres://...): ").strip()
    if not cloud_url:
        print("❌ No URL provided.")
        return

    if cloud_url.startswith("postgres://"):
        cloud_url = cloud_url.replace("postgres://", "postgresql://", 1)
        
    # 2. Cloud Connection (Destination)
    try:
        cloud_engine = create_engine(cloud_url)
        SQLModel.metadata.create_all(cloud_engine) # Ensure tables exist
        print("✅ Connected to Cloud Database.")
    except Exception as e:
        print(f"❌ Failed to connect to cloud: {e}")
        return

    # 3. Read Local Data
    with Session(local_engine) as local_session:
        news_items = local_session.exec(select(NewsItem)).all()
        interests = local_session.exec(select(UserInterest)).all()
        print(f"📦 Found {len(news_items)} News Items and {len(interests)} Interests locally.")

    # 4. Write to Cloud
    with Session(cloud_engine) as cloud_session:
        # -- Migrate News Items --
        new_count = 0
        skip_count = 0
        
        print("\nMigrating News Items...")
        # Cache existing URLs to avoid slow checks
        existing_urls_stmt = select(NewsItem.url)
        existing_urls = set(cloud_session.exec(existing_urls_stmt).all())
        
        for item in news_items:
            if item.url in existing_urls:
                skip_count += 1
                continue
            
            # Create new instance (without ID, to let Postgres assign new ID)
            new_item = NewsItem(
                title=item.title,
                summary=item.summary,
                url=item.url,
                source=item.source,
                sector=item.sector,
                agency=item.agency,
                published_at=item.published_at,
                is_circular=item.is_circular,
                is_manual=item.is_manual,
                impact_rating=item.impact_rating,
                is_hidden=item.is_hidden,
                is_saved=item.is_saved,
                related_sources=item.related_sources,
                scraped_at=item.scraped_at
            )
            cloud_session.add(new_item)
            new_count += 1
            
        # -- Migrate Interests --
        new_int_count = 0
        print("\nMigrating User Interests...")
        existing_ints = set(cloud_session.exec(select(UserInterest.keyword)).all())
        
        for interest in interests:
            if interest.keyword in existing_ints:
                continue
                
            new_int = UserInterest(
                keyword=interest.keyword,
                score=interest.score,
                last_active=interest.last_active,
                source=interest.source
            )
            cloud_session.add(new_int)
            new_int_count += 1

        print("Committing to Cloud...")
        cloud_session.commit()
        
    print(f"\n✅ Migration Complete!")
    print(f"   News: {new_count} transferred, {skip_count} skipped (duplicates).")
    print(f"   Interests: {new_int_count} transferred.")

if __name__ == "__main__":
    migrate_data()
