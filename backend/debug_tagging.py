import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.abspath("backend"))

try:
    from scraper import AGENCY_SECTOR_MAP, AGENCY_PATTERNS, KEYWORD_MAP, INFERRED_AGENCY_KEYWORDS

    def mock_tagging(title, summary, source):
        print(f"\n--- Testing Item: {title} ---")
        print(f"Source: {source}")
        
        # 1. Detect Agency
        detected_agency = "Unknown"
        
        # Explicit Pattern Check
        for agency, patterns in AGENCY_PATTERNS.items():
            for pat in patterns:
                if pat.lower() in title.lower() or pat.lower() in source.lower():
                    detected_agency = agency
                    print(f"  [+] Match Agency Pattern: {pat} -> {agency}")
                    break
        
        # Inferred Check if Unknown
        if detected_agency == "Unknown":
            for agency, keywords in INFERRED_AGENCY_KEYWORDS.items():
                for kw in keywords:
                    if kw.lower() in title.lower() or kw.lower() in summary.lower():
                        detected_agency = agency
                        print(f"  [+] Match Inferred Keyword: {kw} -> {agency}")
                        break
        
        print(f"  Detected Agency: {detected_agency}")
        
        # 2. Determine Sector
        sector = "Unknown"
        
        # Agency Map Priority
        if detected_agency in AGENCY_SECTOR_MAP:
            sector = AGENCY_SECTOR_MAP[detected_agency]
            print(f"  [+] Agency-Sector Map: {detected_agency} -> {sector}")
        else:
            print("  [!] No Agency-Sector Map found. Using Keywords.")
            
            # Keyword Counting
            scores = {s: 0 for s in KEYWORD_MAP.keys()}
            text = (title + " " + summary).lower()
            
            for s, kws in KEYWORD_MAP.items():
                for kw in kws:
                    if kw in text:
                        scores[s] += 1
                        print(f"    - Keyword Match: '{kw}' -> {s}")
            
            # Get max
            best_sector = max(scores, key=scores.get)
            if scores[best_sector] > 0:
                sector = best_sector
                print(f"  [+] Best Keyword Sector: {sector} ({scores[sector]})")
            else:
                sector = "General"
                
        return sector

    # Test Cases
    print("Running Diagnostics...")
    mock_tagging("Majlis Ugama Islam Singapura Halal Update", "New certification standards...", "MUIS")
    mock_tagging("Halal Certificate Requirements 2025", "Updates for food establishments.", "Straits Times")
    mock_tagging("MUIS Press Release", "Community updates.", "MUIS")

except Exception as e:
    print(f"Error: {e}")
