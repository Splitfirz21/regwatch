import feedparser
import requests
import urllib.parse

def test_time_search(query, time_window):
    print(f"\n--- Testing: {query} ({time_window}) ---")
    
    full_query = f"{query} {time_window}"
    encoded = urllib.parse.quote(full_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-SG&gl=SG&ceid=SG:en"
    
    feed = feedparser.parse(url)
    print(f"Found {len(feed.entries)} entries.")
    
    found = False
    for entry in feed.entries[:10]:
        print(f"- {entry.title} ({entry.published})")
        if "PEP" in entry.title and "Ministry" in entry.title:
            found = True
            print("  [MATCH FOUND]")
            
    if not found:
        print("  [X] Target NOT found.")

test_time_search("pep awards 2025", "when:12m")
test_time_search("pep awards 2025", "") # Control
