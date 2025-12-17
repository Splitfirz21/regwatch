from database import get_session
from models import NewsItem
from sqlmodel import select

def fix_articles():
    session = next(get_session())
    print("Fixing tags...")
    
    updates = [
        {
            "match": "Raising governance standards",
            "sector": "Financial Services",
            "agency": "MAS"
        },
        {
            "match": "Collective sales en bloc",
            "sector": "Real Estate",
            "agency": "MinLaw"
        },
        {
            "match": "cross-border taxis",
            "sector": "Land Transport",
            "agency": "MOT"
        },
        {
            "match": "Self-driving shuttle tests",
            "sector": "Land Transport",
            "agency": "LTA"
        }
    ]
    
    count = 0
    for up in updates:
        items = session.exec(select(NewsItem).where(NewsItem.title.contains(up["match"]))).all()
        for item in items:
            item.sector = up["sector"]
            item.agency = up["agency"]
            session.add(item)
            count += 1
            print(f"Updated '{item.title}' -> {item.sector} | {item.agency}")
            
    session.commit()
    print(f"Done. Fixed {count} items.")

if __name__ == "__main__":
    fix_articles()
