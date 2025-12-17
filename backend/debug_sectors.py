from scraper import classify_sector, extract_agency

def test_sectors():
    tests = [
        ("MTI launches new Digital Economy roadmap.", "MTI", "ICT"), # Exp: ICT, Curr: Wholesale Trade
        ("MOM announces safety measures for construction sites.", "MOM", "Construction"), # Exp: Construction, Curr: Professional Services
        ("MOT reviews air travel bubble arrangements.", "MOT", "Air Transport"), # Exp: Air Transport, Curr: Land Transport
        ("SFA recalls eggs from farm.", "SFA", "Food Services"), # Exp: Food Services (Narrow should stick)
        ("URA releases new property guidelines.", "URA", "Real Estate"), # Exp: Real Estate
        ("Unknown Agency talks about fintech.", "Unknown", "Financial Services")
    ]
    
    print(f"{'Text Snippet':<50} | {'Agency':<8} | {'Current':<20} | {'Target':<20}")
    print("-" * 110)
    
    for text, agency_hint, target in tests:
        # We manually pass agency match to test classify_sector logic specifically
        # In real flow, extract_agency would find it.
        agency = agency_hint
        current = classify_sector(text, agency)
        print(f"{text[:47]:<50} ... | {agency:<8} | {current:<20} | {target:<20}")

if __name__ == "__main__":
    test_sectors()
