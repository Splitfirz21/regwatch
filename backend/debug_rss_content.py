import feedparser
from bs4 import BeautifulSoup
import requests
import html

def debug_feed():
    # Use the query from the screenshot
    query = "mnd speech redas"
    encoded = requests.utils.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-SG&gl=SG&ceid=SG:en"
    
    print(f"Fetching: {url}")
    feed = feedparser.parse(url)
    
    print(f"Entries found: {len(feed.entries)}\n")
    
    for i, entry in enumerate(feed.entries[:3]):
        print(f"--- Entry {i+1} ---")
        print(f"Raw Title: {entry.title!r}")
        
        raw_summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
        print(f"Raw Summary: {raw_summary!r}")
        
        # Test Cleaning Logic 1 (Current)
        soup = BeautifulSoup(raw_summary, 'lxml')
        cleaned_1 = soup.get_text()[:300]
        print(f"Cleaned (Current): {cleaned_1!r}")
        
        # Test Cleaning Logic 2 (Unescape first)
        unescaped = html.unescape(raw_summary)
        soup2 = BeautifulSoup(unescaped, 'lxml')
        cleaned_2 = soup2.get_text()[:300]
        print(f"Cleaned (Unescaped): {cleaned_2!r}")

debug_feed()
