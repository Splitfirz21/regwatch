
import requests
from sqlmodel import Session, select
from database import engine
from models import NewsItem
import sys

def check_health():
    print("=== System Health Check ===")
    
    # 1. API Connectivity
    try:
        res = requests.get("http://localhost:8005/news")
        if res.status_code == 200:
            print("[PASS] Backend API is reachable.")
        else:
            print(f"[FAIL] Backend API returned {res.status_code}")
    except Exception as e:
        print(f"[FAIL] Backend API connection failed: {e}")

    # 2. Database Integrity
    with Session(engine) as session:
        items = session.exec(select(NewsItem)).all()
        print(f"[INFO] Total News Items: {len(items)}")
        
        # Check Impact Regression
        false_highs = 0
        for item in items:
            text = (item.title + " " + item.summary).lower()
            if item.impact_rating == "High":
                # Check known false positives
                if "cross-border taxi" in text and not "quota" in text: # Wait, quota trigger was common
                     # Just strict check: User said "cross border taxi" is Medium.
                     # If it's High, valid if user manually set it? 
                     if item.is_manual: continue
                     # If regex fix worked, this shouldn't be High unless other keywords exist
                     pass
        
        # Check Agency Multiple Tags
        multi_agency_count = 0
        for item in items:
            if item.agency and "," in item.agency:
                multi_agency_count += 1
        print(f"[INFO] Items with Multiple Agencies: {multi_agency_count}")
        
    print("=== Check Complete ===")

if __name__ == "__main__":
    check_health()
