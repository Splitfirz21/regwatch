
from sqlmodel import Session, select
from database import engine
from models import NewsItem
import scorer

def reclassify_impact():
    print("Running Impact Reclassification...")
    
    with Session(engine) as session:
        items = session.exec(select(NewsItem)).all()
        print(f"Checking {len(items)} items...")
        
        upgraded_count = 0
        total_high = 0
        
        for item in items:
            old_impact = item.impact_rating
            # Re-run scorer
            new_impact = scorer.analyze_impact(item.title, item.summary)
            
            if new_impact != old_impact:
                item.impact_rating = new_impact
                session.add(item)
                print(f"  [UPDATE] {item.title[:50]}... : {old_impact} -> {new_impact}")
                if new_impact == "High":
                    upgraded_count += 1
            
            if new_impact == "High":
                total_high += 1
                
        session.commit()
        print("-" * 50)
        print(f"Reclassification Complete.")
        print(f"Upgraded to High: {upgraded_count}")
        print(f"Total High Impact Items: {total_high}")

if __name__ == "__main__":
    reclassify_impact()
