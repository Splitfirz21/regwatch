import feedparser
import requests
import urllib.parse

def test_global_filter(query):
    # Global SG Search URL
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-SG&gl=SG&ceid=SG:en"
    print(f"URL: {url}")
    
    feed = feedparser.parse(url)
    print(f"Found {len(feed.entries)} entries.")
    
    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link
        
        source_guess = "Google News"
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            title_only = parts[0]
            source_guess = parts[1]
        else:
            title_only = title
            
        print(f"\nItem: {title}")
        print(f"  Source Guess: '{source_guess}'")
        print(f"  Link: {link}")
        
        # LOGIC TO TEST
        is_sg_likely = ".sg" in link or "Singapore" in title or "Ministry" in source_guess or any(s in link for s in ["straitstimes", "channelnewsasia", "todayonline", "businesstimes"])
        
        print(f"  -> Passes Filter? {is_sg_likely}")
        
        if "PEP" in title and "2025" in title:
            print("  [!!!] THIS IS THE TARGET ARTICLE")

test_global_filter("pep awards 2025")
