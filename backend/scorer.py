
# Heursitic Scorer for Regulatory News

IMPACT_KEYWORDS = {
    "High": [
        "act", "bill", "law", "penalty", "fine", "charged", "revoked", "banned", "jail", 
        "sentence", "convicted", "obligation", "compliance", "mandatory", "enforcement", 
        "raid", "seize", "court", "prosecute", "license revoked", "suspension", "stop order",
        # Operational/Regulatory Changes (User Request)
        "certification", "certificate", "certificates", "licence", "license", "licences", "licenses", "permit", "permits", 
        "quota", "levy", "hours", "curfew", "mask", "masks", "vaccination", "testing", "safe management", 
        "site selection", "zoning", "redevelopment", "digitalisation", "digitisation",
        "lifted", "relaxed", "eased", "tightened", "extended", "expanded", "restricted"
    ],
    "Medium": [
        "consultation", "proposal", "guideline", "framework", "standard", "review", 
        "mou", "agreement", "initiative", "grant", "subsidy", "support scheme", 
        "advisory", "circular", "direction", "reminder", "speech", "parliament",
        "dialogue", "forum", "visit", "roadmap", "blueprint"
    ],
    "Low": [
        "dinner", "award", "appreciation", "festival", "charity", 
        "donation", "community", "celebration", "anniversary", "closure", 
        "maintenance", "service disruption"
    ]
}

import re

def analyze_impact(title: str, summary: str) -> str:
    """Classify news item impact based on keywords."""
    text = (title + " " + summary).lower()
    
    # 0. User Specific Overrides (Learning)
    # "cross border taxis is considered medium"
    if "cross-border taxi" in text or "cross border taxi" in text:
        return "Medium"
    # "investing billions" -> Medium (unless Act passed)
    if "invest" in text and "billion" in text and "act" not in text and "law" not in text:
        return "Medium"
        
    # "Consumer Watchdog" / "Unfair Practices" -> Low (Specific Company Enforcement)
    if ("watchdog" in text or "consumer" in text or "cccs" in text) and ("unfair" in text or "misleading" in text or "warns" in text):
        return "Low"

    # 1. Check High
    for k in IMPACT_KEYWORDS["High"]:
        # Use simple word boundary regex to avoid "billion" matching "bill" or "attractive" matching "act"
        # Escape k to handle special chars if any
        pattern = r'\b' + re.escape(k) + r'\b'
        if re.search(pattern, text):
            return "High"
    
    # 2. Check Medium
    for k in IMPACT_KEYWORDS["Medium"]:
        pattern = r'\b' + re.escape(k) + r'\b'
        if re.search(pattern, text):
            return "Medium"
            
    # 3. Check Low (Explicit)
    for k in IMPACT_KEYWORDS["Low"]:
        pattern = r'\b' + re.escape(k) + r'\b'
        if re.search(pattern, text):
            return "Low"
        
    # Default to Medium if "Ministry" or "Agency" involved, else Low
    return "Medium" 
