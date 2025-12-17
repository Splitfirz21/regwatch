import requests
import json

url = "http://localhost:8000/items"
payload = {
    "title": "Debug Article",
    "summary": "This is a test summary",
    "url": "http://example.com/debug",
    "source": "Debug Source",
    "sector": "General",
    "agency": "DOC",
    "published_at": "2025-12-06T00:00:00",
    "scraped_at": "2025-12-06T00:00:00",
    "is_circular": False
}

print("Sending payload:", json.dumps(payload, indent=2))
try:
    res = requests.post(url, json=payload)
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Error:", e)
