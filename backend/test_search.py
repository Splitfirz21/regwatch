from scraper import search_news

query = "autonomous bus punggol"
print(f"Testing Query: '{query}'")
items = search_news(query)
print(f"Found {len(items)} items.")
for i in items:
    print(f" - {i.title} ({i.url})")
