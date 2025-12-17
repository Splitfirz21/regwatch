import sys
import os
import feedparser # ensure accessible if needed inside scraper (it is)

# Add the backend directory to sys.path
sys.path.append(os.path.abspath("backend"))

try:
    import scraper
    
    query = "dpm speech at pep awards 2025 on regulations"
    print(f"Testing Query: '{query}'")
    
    # We want to see what's happening inside.
    # Since we can't easily hook into print statements of the running server without logs,
    # running this script will execute the code in `scraper.py` directly and show its prints.
    
    result = scraper.search_news(query)
    
    print(f"\nFinal Result Summary: {result['summary']}")
    print(f"Total Items: {len(result['items'])}")
    
    for idx, item in enumerate(result['items']):
        print(f"\n--- Rank {idx+1} ---")
        print(f"Title: {item.title}")
        print(f"Source: {item.source}")
        print(f"URL: {item.url}")
        
except Exception as e:
    print(f"Error during reproduction: {e}")
