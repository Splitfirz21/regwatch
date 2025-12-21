import google.generativeai as genai
import os
import time
from sqlmodel import Session, select, text
from database import engine
from models import NewsItem
from pgvector.sqlalchemy import Vector

# Backfill Embeddings for Level 3 Search
# Requires GOOGLE_API_KEY env var

def backfill():
    print("🧠 Starting Embedding Backfill (Level 3 Upgrade)...")
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found. Please set it.")
        return
        
    genai.configure(api_key=api_key)
    
    with Session(engine) as session:
        # Get all items without embeddings
        # Since embedding is a new column, it will be None for everyone
        # We can just fetch all.
        items = session.exec(select(NewsItem).where(NewsItem.is_hidden == False)).all()
        print(f"📦 Found {len(items)} items to process.")
        
        count = 0
        success = 0
        
        for item in items:
            # Check if embedding already exists (if we re-run)
            # Depending on how sqlalchemy mapped it, it might be None or empty list
            if item.embedding:
                continue

            try:
                # Combine Title + Summary for rich context
                text_content = f"{item.title} {item.summary or ''}"
                
                # Call Gemini API
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text_content,
                    task_type="retrieval_document" 
                )
                
                # Save
                item.embedding = result['embedding']
                session.add(item)
                
                success += 1
                count += 1
                
                # Commit every 10 items to save progress
                if count % 10 == 0:
                    session.commit()
                    print(f"   Processed {count} items...")
                    
                # Rate Limit Safety (Gemini Free is 15 RPM? No, standard is higher but simpler to be safe)
                # 60 RPM -> 1 per sec usually safe. Flash is very generous.
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"   ⚠️ Failed for ID {item.id}: {e}")
                # Continue to next
                
        session.commit()
        print(f"✅ Backfill Complete! Enhanced {success} items with AI Vectors.")

if __name__ == "__main__":
    backfill()
