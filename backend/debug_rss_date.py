import feedparser
import requests
from datetime import datetime
import time
from dateutil import parser as date_parser

def test_rss_date():
    user_query = "Planning for senior living needs rethink"
    # Raw search to get the LINK
    full_query = f'"{user_query}" site:businesstimes.com.sg'
    
    encoded = requests.utils.quote(full_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-SG&gl=SG&ceid=SG:en"
    
    encoded = requests.utils.quote(full_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-SG&gl=SG&ceid=SG:en"
    
    print(f"Fetching: {url}")
    feed = feedparser.parse(url)
    
    found = False
    with open("titles.txt", "w") as f:
        for i, entry in enumerate(feed.entries):
            f.write(f"{i}: {entry.title}\n")
            if "rethink" in entry.title.lower():
                found = True
                print(f"FOUND at index {i}")
                print(f"Raw Published: {getattr(entry, 'published', 'MISSING')}")
            
    if not found:
        print("Target article NOT found in checking first page of results.")

if __name__ == "__main__":
    test_rss_date()
