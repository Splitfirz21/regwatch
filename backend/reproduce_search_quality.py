import sys
import os
import json
from datetime import datetime

# Add the backend directory to sys.path
sys.path.append(os.path.abspath("backend"))

try:
    import scraper
    
    query = "dpm speech at pep awards 2025 on regulations"
    print(f"Testing Query: '{query}'")
    
    result = scraper.search_news(query)
    
    print(f"\nSummary: {result['summary']}")
    print(f"Items Found: {len(result['items'])}")
    
    for idx, item in enumerate(result['items']):
        print(f"\n--- Item {idx+1} ---")
        print(f"Title: {item.title}")
        print(f"URL: {item.url}")
        print(f"Source: {item.source}")
        
except Exception as e:
    print(f"Error: {e}")
