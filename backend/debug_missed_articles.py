from scraper import classify_sector, extract_agency, RELEVANCE_KEYWORDS, EXCLUSION_KEYWORDS, SINGAPORE_CONTEXT_KEYWORDS, AGENCY_PATTERNS
import re

# Test cases based on user feedback
articles = [
    {
        "title": "Raising governance standards for smaller firms and retail investors",
        "summary": "Focus on corporate governance, compliance, and standards for small companies in Singapore.",
        "url": "https://www.businesstimes.com.sg/companies-markets/raising-governance-standards-smaller-firms-retail-investors",
        "source": "The Business Times"
    },
    {
        "title": "Collective sales en bloc regime under review by MinLaw; majority threshold being looked at",
        "summary": "The Ministry of Law (MinLaw) is reviewing the en bloc sales regime and considering changes to the majority threshold in Singapore.",
        "url": "https://www.channelnewsasia.com/singapore/collective-sales-en-bloc-regime-under-review-minlaw-majority-threshold-5479956",
        "source": "CNA"
    },
    {
        "title": "Self-driving shuttle tests to intensify in Punggol in preparation for passenger service in 2026",
        "summary": "Autonomous vehicle testing regulations and safety assessments are ramping up in Singapore.",
        "url": "https://www.straitstimes.com/singapore/transport/self-driving-shuttle-tests-to-intensify-in-punggol-in-preparation-for-passenger-service-in-2026",
        "source": "The Straits Times"
    },
    {
        "title": "Board of critical services operators will need cyber security training, have greater responsibility",
        "summary": "New regulatory requirements for cybersecurity training for board members of critical information infrastructure in Singapore.",
        "url": "https://www.straitstimes.com/tech/board-of-critical-services-operators-will-need-cyber-security-training-have-greater-responsibility",
        "source": "The Straits Times"
    },
    {
        "title": "Singapore-Malaysia cross-border taxis can drop passengers anywhere; buses to get more flexible",
        "summary": "New agreement on cross-border transport regulations allowing taxis to drop off anywhere.",
        "url": "https://www.channelnewsasia.com/asia/singapore-malaysia-cross-border-taxis-drop-passengers-anywhere-buses-transport-5559201",
        "source": "CNA"
    }
]

def local_is_relevant(text, is_gov_source=False):
    text_lower = text.lower()
    print(f"DEBUG: Checking '{text[:50]}...'")
    
    # 1. Exclusions
    for kw in EXCLUSION_KEYWORDS:
        if kw in text_lower:
            print(f"  -> EXCLUDED by '{kw}'")
            return False
            
    # 2. Keywords
    has_regulatory_keyword = False
    for kw in RELEVANCE_KEYWORDS:
        if kw in text_lower:
            print(f"  -> MATCHED KEYWORD '{kw}'")
            has_regulatory_keyword = True
            break
            
    if not has_regulatory_keyword:
        print("  -> NO REGULATORY KEYWORD")
        return False

    # 3. Agency
    extracted_agency = extract_agency(text)
    has_agency_name = extracted_agency != "Unknown"
    print(f"  -> Agency: {extracted_agency}")
    
    # 4. Context
    if is_gov_source:
        print("  -> GOV Source Auto-Pass")
        return True
        
    has_sg_context = False
    for kw in SINGAPORE_CONTEXT_KEYWORDS:
         if kw == "sg":
             if re.search(r'\bsg\b', text_lower):
                 has_sg_context = True
                 print(f"  -> Context Match 'sg'")
                 break
         elif kw in text_lower:
             has_sg_context = True
             print(f"  -> Context Match '{kw}'")
             break
    
    if not has_sg_context:
        print("  -> NO SG CONTEXT")

    if has_agency_name:
        has_strict_acronym = False
        for code in AGENCY_PATTERNS:
            if re.search(r'\b' + re.escape(code.lower()) + r'\b', text_lower):
                has_strict_acronym = True
                print(f"  -> Scrict Acronym '{code}'")
                break
        
        if has_strict_acronym:
            print("  -> Pass: Agency with Strict Acronym")
            return True
        if has_sg_context:
            print("  -> Pass: Agency with SG Context")
            return True
        print("  -> Agency found but weak context")
        return False

    if has_sg_context:
        print("  -> Pass: No Agency but Reg Keyword + SG Context")
        return True

    return False

print("--- Analyzing Missed Articles ---")
for art in articles:
    full_text = f"{art['title']} {art['summary']} {art['source']}"
    
    relevant = local_is_relevant(full_text, is_gov_source=False)
    
    print(f"Title: {art['title']}")
    print(f"Relevant: {relevant}\n")
