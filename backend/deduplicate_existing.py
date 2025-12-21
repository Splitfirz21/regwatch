import os
from sqlmodel import Session, select
from difflib import SequenceMatcher
from database import engine
from models import NewsItem
from datetime import datetime

# Set this env var to your cloud DB URL before running if targeting cloud
# os.environ["DATABASE_URL"] = "..." 

def deduplicate():
    print("Starting deduplication of existing records...")
    with Session(engine) as session:
        # Fetch all visible items
        # Sort by ID asc so we keep the older ones (or desc to keep newer? usually keep older as primary)
        items = session.exec(select(NewsItem).where(NewsItem.is_hidden == False).order_by(NewsItem.published_at.desc())).all()
        
        print(f"Checking {len(items)} items for duplicates...")
        
        # We will iterate and build a list of "kept" items to check against
        kept_items = []
        updates = 0
        hidden_count = 0
        
        for item in items:
            # Check against already kept items
            found_match = None
            normalized_title = item.title.lower()
            
            for kept in kept_items:
                # 1. Exact URL (Shouldn't happen if logic was right, but good safety)
                if kept.url == item.url:
                    found_match = kept
                    break
                
                # 2. Fuzzy Title
                ratio = SequenceMatcher(None, normalized_title, kept.title.lower()).ratio()
                if ratio > 0.65:
                    found_match = kept
                    print(f"Found Duplicate: '{item.title}' (~ '{kept.title}')")
                    break
            
            if found_match:
                # Merge 'item' into 'found_match'
                # item will be hidden
                
                if found_match.related_sources is None:
                    found_match.related_sources = []
                
                # Check duplication in sources
                existing_urls = {s.get('url') for s in found_match.related_sources}
                existing_urls.add(found_match.url)
                
                if item.url not in existing_urls:
                    new_source = {
                        "source": item.source,
                        "url": item.url,
                        "date": item.published_at.isoformat() if item.published_at else None
                    }
                    # We need to re-assign the list for SQLModel to detect change
                    new_list = list(found_match.related_sources)
                    new_list.append(new_source)
                    found_match.related_sources = new_list
                    
                    session.add(found_match)
                    
                    # Mark current item as hidden (soft delete)
                    item.is_hidden = True
                    session.add(item)
                    
                    updates += 1
                    hidden_count += 1
            else:
                # No match found, keep this item as unique
                kept_items.append(item)
        
        session.commit()
        print(f"Finished! Merged {hidden_count} duplicates into parent articles.")

if __name__ == "__main__":
    deduplicate()
