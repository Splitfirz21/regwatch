from scraper import search_news
import logging
import sys

print("--- START DEBUG SEARCH ---")
results = search_news("MUIS digital halal certificate")
print(f"--- FOUIND {len(results)} ITEMS ---")
for item in results:
    print(f"Title: {item.title}")
    print(f"URL: {item.url}")
    print(f"Agency: {item.agency}")
    print(f"Sector: {item.sector}")
    print(f"Pub Date: {item.published_at}")
    print(f"Full Summary: {item.summary}")
    print("-" * 20)
print("--- END DEBUG SEARCH ---")
