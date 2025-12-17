import feedparser
import requests
import urllib.parse
from datetime import datetime

def test_search(label, query, use_sites=False):
    print(f"\n--- Testing: {label} ---")
    
    if use_sites:
        sites = " OR ".join([f"site:{s}" if "site" not in s else s for s in ["straitstimes.com", "channelnewsasia.com", "businesstimes.com.sg", "theedgesingapore.com", ".gov.sg"]])
        full_query = f"({query}) ({sites})"
    else:
        full_query = query
        
    print(f"Query: {full_query}")
    
    encoded = urllib.parse.quote(full_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-SG&gl=SG&ceid=SG:en"
    print(f"URL: {url}")
    
    try:
        feed = feedparser.parse(url)
        print(f"Found {len(feed.entries)} entries.")
        
        found_target = False
        for i, entry in enumerate(feed.entries[:10]):
            print(f"[{i+1}] {entry.title} ({entry.link})")
            if "mti.gov.sg" in entry.link and "speech" in entry.link:
                 found_target = True
                 print("  [!!!] MATCH")
            elif "PEP" in entry.title and "2025" in entry.title:
                 found_target = True
                 print("  [!!!] MATCH")

        if not found_target:
            print("  [X] Target NOT found.")
            
    except Exception as e:
        print(f"Error: {e}")

# Exact keywords user used (logic extracts "pep awards 2025")
fallback_query = "pep awards 2025"

test_search("Restricted Fallback", fallback_query, use_sites=True)
test_search("Global Fallback", fallback_query, use_sites=False)
