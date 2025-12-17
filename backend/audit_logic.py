from scraper import extract_agency, classify_sector, is_relevant_business_news, AGENCY_SECTOR_MAP

def audit():
    print("--- Audit: Singapore Context Logic ---")
    
    # Case 1: UK Minister (Generic Role, Foreign Context)
    # Expected: Should be REJECTED (False) or Agency="Unknown" if we implement strict checks.
    # Current: Likely "MTI" (due to 'Trade') and Relevant=True.
    text_foreign = "UK Minister for Trade announces new tariff rules."
    agency_f = extract_agency(text_foreign)
    relevant_f = is_relevant_business_news(text_foreign, is_gov_source=False)
    print(f"Foreign Text: '{text_foreign}'")
    print(f"  Agency: {agency_f}")
    print(f"  Relevant: {relevant_f} (Expected: False)")
    
    # Case 2: SG Minister (Generic Role, Implicit SG Context from ST?)
    # If text has "Singapore", it should be True.
    text_sg = "Minister for Trade announced new Singapore tariff rules."
    agency_sg = extract_agency(text_sg)
    relevant_sg = is_relevant_business_news(text_sg, is_gov_source=False)
    print(f"SG Text: '{text_sg}'")
    print(f"  Agency: {agency_sg}")
    print(f"  Relevant: {relevant_sg} (Expected: True)")
    
    # Case 3: Ambiguous (ST article, no SG keyword, just "Minister for Trade")
    text_amb = "Minister for Trade said compliance is key for businesses."
    agency_amb = extract_agency(text_amb)
    relevant_amb = is_relevant_business_news(text_amb, is_gov_source=False)
    print(f"Ambiguous Text: '{text_amb}'")
    print(f"  Agency: {agency_amb}")
    print(f"  Relevant: {relevant_amb} (Expected: ?)")
    
    # Case 4: US "Secretary of State" (Should fail Role check?)
    text_us = "US Secretary of State speaks on policy."
    agency_us = extract_agency(text_us)
    relevant_us = is_relevant_business_news(text_us, is_gov_source=False)
    print(f"US Text: '{text_us}'")
    print(f"  Agency: {agency_us}")
    print(f"  Relevant: {relevant_us} (Expected: False)")

if __name__ == "__main__":
    audit()
