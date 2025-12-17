import feedparser
import requests
import urllib.parse
from datetime import datetime
import time

def test_exact(query_str):
    print(f"\n--- Testing: {query_str} ---")
    
    # Replicate scraper.py site string exactly
    sites = " OR ".join([f"site:{s}" if "site" not in s else s for s in ["straitstimes.com", "channelnewsasia.com", "businesstimes.com.sg", "theedgesingapore.com", ".gov.sg"]])
    
    full_query = f"({query_str}) ({sites})"
    print(f"Full Query: {full_query}")
    
    encoded = urllib.parse.quote(full_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-SG&gl=SG&ceid=SG:en"
    print(f"URL: {url}")
    
    try:
        feed = feedparser.parse(url)
        print(f"Found {len(feed.entries)} entries.")
        
        for i, entry in enumerate(feed.entries[:10]):
            print(f"[{i+1}] {entry.title}")
            print(f"     Link: {entry.link}")
            if "mti.gov.sg" in entry.link or "PEP" in entry.title:
                print("     [MATCH FOUND!]")
                
    except Exception as e:
        print(f"Error: {e}")

# Test the extracted tokens
test_exact("pep awards 2025")

# Test without '2025'
test_exact("pep awards")

# Test original loose
test_exact("dpm speech pep awards 2025")
