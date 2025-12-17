from scraper import search_news, extract_agency, classify_sector, is_relevant_business_news, AGENCY_SECTOR_MAP, RELEVANCE_KEYWORDS
from datetime import datetime

def test_st_tagging():
    print("\n=== DEBUG: ST Article Tagging ===")
    # Try to find the actual article to see real text
    items = search_news("Food handlers mask Straits Times")
    found = False
    for item in items:
        if "Food handler" in item.title or "mask" in item.title:
            found = True
            print(f"FAILED ITEM FOUND: {item.title}")
            print(f"  URL: {item.url}")
            print(f"  Summary: {item.summary}")
            print(f"  Agency: {item.agency}")
            print(f"  Sector: {item.sector}")
            
            # Re-run extraction explicitly on full text
            full_text = f"{item.title} {item.summary} {item.source or ''}"
            print(f"  [Re-Check] extracted_agency: '{extract_agency(full_text)}'")
            print(f"  [Re-Check] classify_sector: '{classify_sector(full_text, extract_agency(full_text))}'")
            
            # Check for Full Name vs Acronym
            if "Singapore Food Agency" in full_text:
                print("  [DEBUG] 'Singapore Food Agency' found in text.")
            if "SFA" in full_text:
                print("  [DEBUG] 'SFA' found in text.")
                
            break
            
    if not found:
        print("Could not find ST article via search. Using mock...")
        mock_text = "Food handlers will no longer need to wear masks. The Singapore Food Agency (SFA) announced the change."
        print(f"Mock Text: {mock_text}")
        agency = extract_agency(mock_text)
        print(f"  Agency: {agency}")
        print(f"  Sector: {classify_sector(mock_text, agency)}")

def test_gov_speeches():
    print("\n=== DEBUG: Gov Speeches Tagging ===")
    # 1. REDAS
    query1 = "Chee Hong Tat REDAS 66th Anniversary"
    print(f"Searching for: '{query1}'")
    items = search_news(query1)
    if items:
        print(f"  FOUND {len(items)} items.")
        for item in items:
            print(f"    - {item.title} ({item.published_at}) [Agency: {item.agency}]")
    else:
        print("  NOT FOUND.")

    # 2. PEP-SBF
    query2 = "Gan Kim Yong PEP-SBF Awards 2025"
    print(f"Searching for: '{query2}'")
    items = search_news(query2)
    if items:
        print(f"  FOUND {len(items)} items.")
        for item in items:
             print(f"    - {item.title} ({item.published_at}) [Agency: {item.agency}]")
             # Check date logic
             days_old = (datetime.utcnow() - item.published_at).days
             print(f"      Age: {days_old} days. (Filter > 30?)")
    else:
        print("  NOT FOUND.")

if __name__ == "__main__":
    test_st_tagging()
    test_gov_speeches()
