import requests
from bs4 import BeautifulSoup
import feedparser

def test_mas_rss():
    url = "https://www.mas.gov.sg/api/v1/rss/media-releases"
    print(f"Testing RSS: {url}")
    f = feedparser.parse(url)
    print(f"Entries: {len(f.entries)}")
    if len(f.entries) > 0:
        print("Sample:", f.entries[0].title)
    else:
        print("RSS Failed or Empty")

def test_mas_html():
    url = "https://www.mas.gov.sg/regulation/circulars"
    print(f"Testing HTML: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        # Look for links containing "Circular"
        links = soup.find_all("a", string=lambda t: t and "Circular" in t)
        print(f"Found {len(links)} links with 'Circular'")
        for l in links[:3]:
            print(f"- {l.get_text().strip()} ({l.get('href')})")
            
        # Try generic article cards if specific circular search fails
        if not links:
            print("Trying generic 'mas-search-card'...")
            cards = soup.find_all("div", class_="mas-search-card")
            print(f"Found {len(cards)} cards")
    except Exception as e:
        print(e)
        
def test_mom_html():
    url = "https://www.mom.gov.sg/newsroom/circulars" 
    print(f"Testing MOM HTML: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        links = soup.select("h3 a") # specific selector guess
        print(f"Found {len(links)} MOM links")
        for l in links[:3]:
            print(f"- {l.get_text().strip()}")
    except Exception as e:
        print(e)

def test_google_rss():
    # Search for circulars from key agencies
    query = "site:gov.sg circular OR site:mas.gov.sg circular OR site:mom.gov.sg circular OR site:iras.gov.sg circular"
    encoded_query = requests.utils.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-SG&gl=SG&ceid=SG:en"
    print(f"Testing Google RSS: {url}")
    f = feedparser.parse(url)
    print(f"Entries: {len(f.entries)}")
    for e in f.entries[:5]:
        print(f"- {e.title} ({e.link})")

if __name__ == "__main__":
    # test_mas_rss()
    # test_mas_html()
    # test_mom_html()
    test_google_rss()
