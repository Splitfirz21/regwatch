
from sqlmodel import Session, select, create_engine
from models import NewsItem, UserInterest
from database import engine
from collections import Counter
import re

def seed_interests_from_dashboard():
    print("Seeding Use Interests from Current Dashboard...")
    
    with Session(engine) as session:
        # 1. Fetch all visible items
        items = session.exec(select(NewsItem).where(NewsItem.is_hidden == False)).all()
        print(f"Analyzing {len(items)} articles...")
        
        # 2. Extract Terms
        interest_scores = Counter()
        
        # Stopwords for title analysis
        stopwords = {"the", "a", "an", "to", "in", "on", "for", "of", "and", "is", "are", "with", "from", "at", "by", "as", "be", "it", "that", "this", "or", "new", "more", "but", "sg", "singapore", "says"}
        
        for item in items:
            # A. Agencies (High Relevance)
            if item.agency and item.agency != "Unknown":
                agencies = item.agency.split(", ")
                for ag in agencies:
                    interest_scores[ag] += 2.0 # High weight for explicit agencies
            
            # B. Sector (Medium Relevance)
            if item.sector and item.sector != "General Business" and item.sector != "General":
                interest_scores[item.sector] += 1.0
                
            # C. Title Keywords (Specific Interest)
            # Simple extraction: Capitalized words (Proper Nouns) + specific regulatory terms
            words = re.findall(r'\b[A-Za-z][a-z-]+\b', item.title) # Simple words
            for w in words:
                w_lower = w.lower()
                if w_lower not in stopwords and len(w) > 3:
                    # Boost specific topics logic
                    if w_lower in ["taxi", "crypto", "solar", "drone", "electric", "shuttle", "worker", "employment", "grant", "levy"]:
                         interest_scores[w_lower] += 1.5
                    else:
                         # statistical accumulation
                         interest_scores[w_lower] += 0.2
                         
        # 3. Upsert to DB
        print(f"Found {len(interest_scores)} potential interests.")
        print(f"Top 10: {interest_scores.most_common(10)}")
        
        count = 0
        for keyword, score in interest_scores.most_common(50): # Cap at top 50 to avoid noise
            if score < 1.0: continue # Min threshold
            
            # Check existing
            existing = session.get(UserInterest, keyword)
            if existing:
                existing.score += score # Add to existing manual searches
                existing.last_active = datetime.utcnow()
                session.add(existing)
            else:
                new_interest = UserInterest(keyword=keyword, score=score, source="dashboard_analysis")
                session.add(new_interest)
            count += 1
            
        session.commit()
        print(f"Successfully seeded {count} interests into the Learning Engine.")

if __name__ == "__main__":
    from datetime import datetime
    seed_interests_from_dashboard()
