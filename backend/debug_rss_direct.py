import feedparser
import requests
import urllib.parse

def test_query(label, query):
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-SG&gl=SG&ceid=SG:en"
    print(f"\n--- Testing: {label} ---")
    print(f"Query: {query}")
    print(f"URL: {url}")
    
    try:
        feed = feedparser.parse(url)
        print(f"Found {len(feed.entries)} entries.")
        found_target = False
        for entry in feed.entries[:5]:
            print(f"- {entry.title} ({entry.link})")
            if "mti.gov.sg" in entry.link or "PEP" in entry.title:
                found_target = True
                print("  [!!!] FOUND TARGET MATCH")
        
        if not found_target and len(feed.entries) > 0:
            # Check deeper if not in top 5
            for entry in feed.entries[5:]:
                if "mti.gov.sg" in entry.link or "PEP" in entry.title:
                    print(f"- {entry.title} ({entry.link})")
                    print("  [!!!] FOUND TARGET MATCH")
                    
    except Exception as e:
        print(f"Error: {e}")

# exact user query words (cleaned)
# "dpm speech pep awards 2025 regulations"

# Variations
test_query("Full Keywords + Sites", "(dpm speech pep awards 2025 regulations) (site:straitstimes.com OR site:channelnewsasia.com OR site:businesstimes.com.sg OR site:theedgesingapore.com OR site:.gov.sg)")

test_query("Targeted Site Only", "(dpm speech pep awards 2025) site:.gov.sg")

test_query("Broad (No Site Limit)", "dpm speech pep awards 2025")

test_query("Very Broad", "PEP Awards 2025")
