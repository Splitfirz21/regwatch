import random
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
from models import NewsItem
from faker import Faker
import time
from database import engine
import re
from dateutil import parser as date_parser
import scorer # Impact logic
from sqlmodel import Session, select
from models import NewsItem, UserInterest
import vector_engine

fake = Faker()

ITM_SECTORS = [
    "Energy & Chemicals", "Precision Engineering", "Electronics", "Aerospace", "Marine & Offshore", 
    "Logistics", "Air Transport", "Land Transport", "Sea Transport", 
    "ICT", "Media", 
    "Food Services", "Retail", "Hotels", 
    "Real Estate", "Security", "Environmental Services", "Wholesale Trade", 
    "Healthcare", "Education", "Professional Services", 
    "Financial Services", "Construction", "General Business"
]

# Simple keyword mapping
KEYWORD_MAP = {
    "General Business": ["business", "sbf", "pep", "pro-enterprise", "enterprise", "sme", "startup", "economy", "economic", "market outlook", "biz", "commerce", "chamber"],
    "Energy & Chemicals": ["energy", "oil", "gas", "chemical", "petroleum", "power", "solar", "green", "sustainability"],
    "Precision Engineering": ["machinery", "precision", "semiconductor", "equipment"],
    "Electronics": ["electronics", "chip", "semiconductor", "wafer"],
    "Aerospace": ["aerospace", "aviation", "airline", "aircraft", "sia", "changi"],
    "Marine & Offshore": ["marine", "offshore", "shipyard", "vessel", "keppel", "sembcorp"],
    "Logistics": ["logistics", "supply chain", "cargo", "freight", "warehouse"],
    "Air Transport": ["air transport", "airport", "flight", "terminal", "aviation", "air travel", "airline"],
    "Land Transport": ["land transport", "mrt", "bus", "rail", "lta", "transport", "self-driving", "autonomous", "shuttle", "chauffeur", "taxi", "private hire", "ride-hailing", "cross-border", "checkpoint", "causeway"],
    "Sea Transport": ["sea transport", "port", "maritime", "shipping", "mpa", "ferry"],
    "ICT": ["ict", "tech", "technology", "digital", "cyber", "software", "ai", "data", "internet", "smart nation"],
    "Media": ["media", "film", "broadcast", "content", "advertising"],
    "Food Services": ["food", "dining", "restaurant", "hawker", "f&b", "halal"],
    "Retail": ["retail", "shopping", "mall", "ecommerce", "consumer"],
    "Hotels": ["hotel", "hospitality", "tourism", "staycation"],
    "Real Estate": ["real estate", "property", "housing", "hdb", "ura", "condo", "land", "redas", "developer", "en bloc", "collective sale", "show-flat"],
    "Security": ["security", "police", "surveillance", "defense", "mha"],
    "Environmental Services": ["environment", "waste", "cleaning", "recycle", "nea", "water", "pub", "mse"],
    "Wholesale Trade": ["wholesale", "trade", "import", "export", "distributor"],
    "Healthcare": ["healthcare", "health", "medical", "hospital", "clinic", "moh", "virus", "disease"],
    "Education": ["education", "school", "university", "moe", "student", "teacher", "academic"],
    "Professional Services": ["professional", "consulting", "legal", "accounting", "audit", "law", "advisory"],
    "Financial Services": ["financial", "finance", "bank", "mas", "insurance", "fintech", "investment", "money", "monetary", "retail investor", "shareholder", "governance standard"],
    "Construction": ["construction", "build", "bca", "infrastructure", "contractor", "built environment"]
}

# Extensive Keyword Mapping for Agencies (Full Name + Acronyms)
AGENCY_PATTERNS = {
    "ACRA": ["ACRA", "Accounting and Corporate Regulatory Authority"],
    "A*STAR": ["A*STAR", "Agency for Science, Technology and Research"],
    "BCA": ["BCA", "Building and Construction Authority"],
    "CPFB": ["CPFB", "CPF", "Central Provident Fund"],
    "CAAS": ["CAAS", "Civil Aviation Authority"],
    "EDB": ["EDB", "Economic Development Board"],
    "EMA": ["EMA", "Energy Market Authority"],
    "ENTERPRISESG": ["Enterprise Singapore", "EnterpriseSG", "ESG"],
    "HSA": ["HSA", "Health Sciences Authority"],
    "HDB": ["HDB", "Housing & Development Board", "Housing and Development Board"],
    "IMDA": ["IMDA", "Info-communications Media Development Authority"],
    "IRAS": ["IRAS", "Inland Revenue Authority"],
    "LTA": ["LTA", "Land Transport Authority"],
    "MAS": ["MAS", "Monetary Authority", "Central Bank"],
    "NEA": ["NEA", "National Environment Agency"],
    "MOH": ["MOH", "Ministry of Health"],
    "MOM": ["MOM", "Ministry of Manpower"],
    "MTI": ["MTI", "Ministry of Trade"],
    "MOF": ["MOF", "Ministry of Finance"],
    "URA": ["URA", "Urban Redevelopment Authority"],
    "PUB": ["PUB", "Public Utilities Board", "National Water Agency"],
    "SFA": ["SFA", "Singapore Food Agency", "Food Agency"],
    "SLA": ["SLA", "Singapore Land Authority"],
    "STB": ["STB", "Singapore Tourism Board"],
    "WSG": ["WSG", "Workforce Singapore"],
    "SSG": ["SSG", "SkillsFuture"],
    "SSG": ["SSG", "SkillsFuture"],
    "MinLaw": ["MinLaw", "Ministry of Law"],
    "MOT": ["MOT", "Ministry of Transport"],
    "MUIS": ["MUIS", "Majlis Ugama Islam Singapura", "Islamic Religious Council"],
    "SBF": ["SBF", "Singapore Business Federation"],
    "Customs": ["Singapore Customs", "Customs"],
    "NRF": ["NRF", "National Research Foundation"],
    "MDDI": ["MDDI", "Ministry of Digital Development and Information", "MCI"], # MCI is old name but relevant
    "MSE": ["MSE", "Ministry of Sustainability and the Environment", "MEWR"],
    "MND": ["MND", "Ministry of National Development"],
}

# Inferred Agency Mapping (Keywords -> Agency)
# To handle cases where agency isn't explicit but topic implies it (User Request)
INFERRED_AGENCY_KEYWORDS = {
    "LTA": ["self-driving", "autonomous", "shuttle", "erp", "coe", "taxi", "private hire", "ride-hailing"],
    "MAS": ["retail investor", "shareholder", "listing rule", "governance standard", "crypto", "monetary", "retail investors", "shareholders", "governance standards"],
    "MinLaw": ["en bloc", "collective sale", "land title", "strata"],
    "MOT": ["cross-border transport", "rts link", "hsr", "vtl", "cross-border taxi", "checkpoint"],
    "SFA": ["food safety", "food recall"],
    "MUIS": ["halal certificate", "halal certificates", "halal certification", "halal logo"],
    "URA": ["show-flat", "developer"],
    "SLA": ["show-flat", "site sourcing"],
}

# Dynamic Ministry Mapping (Role to Agency)
MINISTRY_ROLE_MAP = {
    "Trade": "MTI", "Industry": "MTI",
    "National Development": "MND",
    "Manpower": "MOM",
    "Transport": "MOT",
    "Sustainability": "MSE", "Environment": "MSE",
    "Health": "MOH",
    "Home Affairs": "MHA", "Law": "MinLaw", # Corrected for separate ministry
    "Communication": "MDDI", "Information": "MDDI", "Digital": "MDDI", # Updated to MDDI
    "Finance": "MOF",
    "Culture": "MCCY", "Community": "MCCY", "Youth": "MCCY",
    "Prime Minister": "PMO",
    "Research": "NRF", "Customs": "Customs"
}

# Strong Agency-to-Sector Defaults
AGENCY_SECTOR_MAP = {
    "BCA": "Construction",
    "URA": "Real Estate",
    "HDB": "Real Estate",
    "SLA": "Real Estate",
    "CEA": "Real Estate",
    "LTA": "Land Transport",
    "MPA": "Sea Transport",
    "CAAS": "Air Transport",
    "EMA": "Energy & Chemicals",
    "IMDA": "ICT",
    "CSA": "ICT",
    "GovTech": "ICT",
    "MOH": "Healthcare",
    "HSA": "Healthcare",
    "EDB": "Financial Services", # Often generic, but Investment related
    "MAS": "Financial Services",
    "ACRA": "Professional Services",
    "IRAS": "Professional Services",
    "MOM": "Professional Services", # Manpower/HR falls under Prof Services in ITM loosely or General
    "STB": "Hotels",
    "SFA": "Food Services", 
    "NEA": "Environmental Services",
    "PUB": "Environmental Services",
    "MUIS": "Food Services",
    "ESG": "General Business", 
    "ENTERPRISESG": "General Business",
    "MTI": "General Business", # MTI covers broad economic policy
    "SBF": "General Business",
    "MND": "Real Estate", # National Dev = Housing usually
    "MOM": "Professional Services",
    "MOT": "Land Transport", # Default to Land, could be sea/air
    "Customs": "Wholesale Trade",
    "NRF": "General Business",
    "MDDI": "ICT",
    "MSE": "Environmental Services",
    "MOH": "Healthcare",
    "MHA": "Security",
    "MCCY": "Media", # Loose mapping
    "PMO": "General", # High level
    "MinLaw": "Real Estate", # User requested for En Bloc context
}

# Agencies that cover multiple sectors or where context matters more than the agency itself
BROAD_AGENCIES = ["MTI", "MOM", "MOT", "MSE", "PMO", "ESG", "ENTERPRISESG", "SSG", "WSG"]

# Filters for Business/Regulatory Relevance
RELEVANCE_KEYWORDS = [
    "regulation", "regulatory", "compliance", "policy", 
    "permit", "license", "standard", "circular", "guideline", "framework",
    "law", "act", "bill", "levy", "tax", "grant", "incentive", "scheme",
    "roadmap", "blueprint", "transformation", "digitalisation", "rules", "rule",
    "requirement", "required", "mandatory", "exempt", "exemption", "simplify",
    "measure", "amendment", "revised", "revision",
    "minister", "parliament", "speech",
    "governance", "standards", "review", "regime", "threshold", "test", "trial", 
    "pilot", "training", "responsibility", "cross-border",
    "certificate", "certification", "accreditation", "halal", "iso", "audit"
]

# Strong phrases that are almost always regulatory even if agency is missed
STRONG_REGULATORY_PHRASES = [
    "regulatory change", "new rule", "new law", "law passed", "bill passed",
    "act passed", "changes to", "mandatory for", "no longer required",
    "compliance with", "guidelines", "circular", "raising standards", "under review",
    "will need", "greater responsibility", "tests to intensify"
]

EXCLUSION_KEYWORDS = [
    "lifestyle", "entertainment", "sports", "celebrity", "gossip", 
    "crime", "murder", "accident", "fire", "lottery", "toto", "big sweep",
    "rebate", "voucher", "handout", "bursary", "cash", "payout", "subscribe", 
    "giveaway", "deal", "discount", "promotion", "on sale", "% off", "free", 
    "win", "contest", "lucky draw", "lifestyle", "entertainment", "movie",
    "travel", "holiday", "staycation", "crime", "accident",     # removed "review"
    "murder", "police", "court", "jail", "scam", "cheat", "theft", # removed "fire"
    "robbery", "arrest", "charged", "sentenced", "prison", "fine", "appeal",
    "sports", "football", "soccer", "tennis", "golf", "f1", "racing",
    "league", "cup", "tournament", "olympics", "medal", "athlete", # removed "game", "match"
    "match", "league", "cup", "tournament", "olympics", "medal", "athlete",
    "world", "international", "global", "united states", "united kingdom", "china", "japan", "europe", # removed "us", "uk"
    "america", "asia", "africa", "australia", "nz", "indonesia", # removed "malaysia"
    "thailand", "vietnam", "philippines", "myanmar", "india", "korea", "taiwan",
    "hong kong", "macau", "middle east", "russia", "ukraine", "war", "conflict", # removed "hk"
    "earnings", "net profit", "revenue", "shares", "dividend", "quarterly", 
    "stock market", "market close", "share price", "financial results", "net loss",
    "marathon", "race", "listing", "ipo", "sanction", "sanctions", "appointment", "appointed",
    "broker", "digest", "billionaire", "wealth", "ranking", "survey", "analyst", "buy", "sell", "rating", "top employer"
]
# Removed "travel", "holiday", "staycation" to allow tourism/MOT news.
# Removed "safety" from Security map below to avoid WSH confusion.
# International exclusions above help, but we need positive context too.

SINGAPORE_CONTEXT_KEYWORDS = [
    "singapore", "sg", "local", "islandwide", "nation", "state", "republic",
    "lion city", "merlion", "changi", "jurong", "tuas", "punggol", "tengah", "woodlands", "yishun", "tampines", "sengkang"
]

RSS_FEEDS = {
    "The Straits Times": "https://www.straitstimes.com/news/business/rss.xml", # Business
    "The Straits Times (SG)": "https://www.straitstimes.com/news/singapore/rss.xml", # Home/Singapore
    "CNA": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936", # Business
    "CNA (SG)": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416", # Singapore
}

# 3. STRICT SOURCE WHITELIST
# Only allowed domains: straitstimes.com, channelnewsasia.com, businesstimes.com.sg, theedgesingapore.com, gov.sg
ALLOWED_MATCH_STRINGS = [
    "straitstimes.com", 
    "channelnewsasia.com", 
    "businesstimes.com.sg", 
    "theedgesingapore.com",
    "sbr.com.sg",
    "todayonline.com"
]

def is_allowed_source(url: str, source_name: str = "") -> bool:
    url_lower = url.lower()
    source_lower = source_name.lower()
    
    # Trust Google News query if it's a redirect, but double check source name
    if "news.google.com" in url_lower:
        # If source name is provided, check it
        if source_name:
            # Map common names to domains for checking
            if "straits times" in source_lower: return True
            if "channel newsasia" in source_lower or "cna" in source_lower: return True
            if "business times" in source_lower: return True
            if "business times" in source_lower: return True
            if "edge singapore" in source_lower: return True
            if "business review" in source_lower or "sbr" in source_lower: return True
            if "today" in source_lower: return True
    return False
            
    for allowed in ALLOWED_MATCH_STRINGS:
        if allowed in url_lower:
            return True
            
    # Also check source name just in case
    for allowed in ALLOWED_MATCH_STRINGS:
        if allowed in source_lower:
            return True
            
    return False

def fetch_actual_date_from_url(url: str) -> datetime:
    """Fallback: Scrape the article page for meta date tags if RSS fails."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        # Handle Google News Redirects if needed, but requests usually follows them.
        print(f"  [Deep Scan] Fetching metadata from {url[:50]}...")
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code != 200: return None
        
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Meta tags to check
        meta_date = None
        
        # 1. article:published_time (OpenGraph)
        og_date = soup.find("meta", property="article:published_time")
        if og_date: meta_date = og_date.get("content")
        
        # 2. date (Generic)
        if not meta_date:
            d_tag = soup.find("meta", attrs={"name": "date"})
            if d_tag: meta_date = d_tag.get("content")
            
        # 3. publish-date (Straits Times / BT specific sometimes)
        if not meta_date:
            p_tag = soup.find("meta", attrs={"name": "publish-date"})
            if p_tag: meta_date = p_tag.get("content")
            
        if meta_date:
            try:
                dt = date_parser.parse(meta_date)
                print(f"  [Deep Scan] Found date: {dt}")
                return dt
            except: pass
            
    except Exception as e:
        print(f"  [Deep Scan] Failed: {e}")
        return None
    return None

def calculate_relevance_score(text: str, is_gov_source: bool = False) -> int:
    """
    Calculates a relevance score based on weighted semantic signals.
    Threshold: 15 points.
    """
    score = 0
    text_lower = text.lower()
    
    # 1. Government Source Boost (+15)
    if is_gov_source:
        score += 15 
    
    # 2. Strong Regulatory Signals (+10 each)
    strong_signals = [
        "bill passed", "act passed", "new law", "new rule", "regulatory framework",
        "compliance", "mandatory", "legislative", "parliament", "amendment",
        "grant", "subsidy", "levy", "tax", "transformation map", "roadmap",
        "budget", "minister", "circular", "guideline", "standard", "certification"
    ]
    for sig in strong_signals:
        if sig in text_lower:
            score += 10
            if score > 30 and not is_gov_source: break 

    # 3. Agency Presence (+5)
    for agency in AGENCY_PATTERNS.keys():
        if agency.lower() in text_lower:
            score += 5
            break 

    # 4. Singapore Context (+5)
    # Critical for non-gov sources
    if any(kw in text_lower for kw in SINGAPORE_CONTEXT_KEYWORDS):
        score += 5

    # 5. Business Impact Signals (+5)
    impact_signals = [
        "businesses", "smes", "employers", "industry", "sector", "deadline",
        "eligibility", "criteria", "adopt", "roll out", "launch", "apply"
    ]
    if any(s in text_lower for s in impact_signals):
        score += 5

    # 6. Noise & Financial Penalties (-15 to -20) (Strict)
    financial_noise = [
        "market close", "share price", "stock", "equity", "ipo", "listing",
        "dividend", "earnings", "profit", "revenue", "quarterly", "analyst",
        "buy rating", "sell rating", "target price", "broker", "investor",
        "wealth", "billionaire", "rich list", "ranking", "survey", "marathon",
        "race", "sport", "football", "sanction", "iran", "russia", "war"
    ]
    for noise in financial_noise:
        if noise in text_lower:
            score -= 20 # Increased penalty to kill noise
            
    # 7. Geographic Penalties (-10)
    foreign_context = [
        "united states", "usa", "video", "london", "uk", "china", "japan",
        "malaysia", "thailand", "vietnam", "australia", "hong kong"
    ]
    if any(c in text_lower for c in foreign_context):
        if not any(x in text_lower for x in ["cross-border", "trade", "export", "import", "agreement"]):
            score -= 10

    return score

def is_relevant_business_news(text: str, is_gov_source: bool = False) -> bool:
    score = calculate_relevance_score(text, is_gov_source)
    # Threshold: 10
    # Allows "Agency" (5) + "Context" (5) = 10 -> Pass
    # "New Law" (10) -> Pass
    # "IPO" (-20) -> Fail
    return score >= 10

    return False

# For gov.sg we'll use simulation for now or simple HTML check if requests succeed
# But for the task, let's try a direct scrape of gov.sg news section or fallback to simulation if fails.

def classify_sector(text: str, agency: str = "Unknown") -> str:
    # 0. Keyword Scoring (Calculate first to enable Hybrid decisions)
    text_lower = text.lower()
    scores = {}
    for sector, keywords in KEYWORD_MAP.items():
        score = 0
        for kw in keywords:
            # Use Regex Word Boundary to avoid "tech" matching "fintech" or "biotech"
            # Escape the keyword to handle "+" (e.g. "c++" or similar if any)
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                score += 1
        if score > 0:
            scores[sector] = score
    
    best_keyword_sector = max(scores, key=scores.get) if scores else "General"

    # Hybrid Logic
    if agency and agency != "Unknown":
        # Handle multiple agencies "URA, SLA"
        agencies = agency.split(", ")
        
        # Priority Check: If any agency is a "Narrow" agency, use its sector.
        # Otherwise use keyword score.
        
        assigned_sector = None
        for ag in agencies:
            if ag in AGENCY_SECTOR_MAP:
                # If it's a Broad Agency, we prefer Keyword Sector IF it exists.
                if ag in BROAD_AGENCIES:
                    if scores:
                        assigned_sector = best_keyword_sector
                    else:
                        assigned_sector = AGENCY_SECTOR_MAP[ag]
                else:
                    # Narrow Agency -> Force Sector (Override Broad)
                    return AGENCY_SECTOR_MAP[ag]
                    
        if assigned_sector:
            return assigned_sector
            
        # Fallback
        if agencies[0] in AGENCY_SECTOR_MAP:
            return AGENCY_SECTOR_MAP[agencies[0]]
            
    # 3. No Agency or Unknown Agency -> use Keywords
    if scores:
        return best_keyword_sector
    
    return "General"

def extract_agency(text: str) -> str:
    # Find ALL matches
    found_agencies = set()
    text_upper = text.upper()
    text_lower = text.lower()
    
    # 1. Acronym Matches
    for code in AGENCY_PATTERNS: # Iterate over keys (acronyms)
        pattern = r'\b' + re.escape(code) + r'\b'
        if re.search(pattern, text_upper):
            found_agencies.add(code)
    
    # 2. Role Matches
    role_match = re.search(r"Minister (?:of State |for |of )?([\w\s&]+)", text, re.IGNORECASE)
    if role_match:
        role_text = role_match.group(1)
        for key, agency in MINISTRY_ROLE_MAP.items():
            if key.lower() in role_text.lower():
                found_agencies.add(agency)
                
    # 3. Inferred Agencies (If still Unknown or to augment)
    # Check for strong topic keywords that imply an agency
    # Only if we haven't found a strong agency? Or additive? 
    # User wanted "Raising governance" -> MAS. 
    # Let's make it additive for now.
    for agency, keywords in INFERRED_AGENCY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                 found_agencies.add(agency)

    if found_agencies:
        return ", ".join(sorted(list(found_agencies)))

    return "Unknown"

def fetch_rss_news(source_name: str, url: str) -> List[NewsItem]:
    print(f"Fetching RSS: {source_name}")
    items = []
    try:
        # Set User Agent to avoid blocking on Cloud (Render)
        feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]: # Limit to 10
            title = entry.title
            summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            # Clean summary html
            import html
            summary = html.unescape(summary) # Unescape first to handle &lt; cases
            soup = BeautifulSoup(summary, 'lxml')
            text_content = soup.get_text().strip()
            summary_text = text_content[:300] + ("..." if len(text_content) > 300 else "")
            
            link = entry.link
            
            # Robust Date Parsing
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            elif hasattr(entry, 'published'):
                try: pub_date = date_parser.parse(entry.published)
                except: pass
            elif hasattr(entry, 'updated'):
                try: pub_date = date_parser.parse(entry.updated)
                except: pass
            
            if not pub_date:
                # print(f"  [DATE WARNING] Could not parse date for '{title}'. Defaulting to NOW.")
                pub_date = datetime.utcnow()
             
            # Combined text for analysis
            full_text = title + " " + summary_text
            
            # Filter: 30 days window (User requirement)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            if pub_date < cutoff_date:
                # print(f"Skipping old article: {title} ({pub_date})")
                continue
            
            # Apply Filter
            if "MyCareersFuture" in source_name or "MyCareersFuture" in title:
                continue
            # Strict Domain Whitelist
            if not is_allowed_source(link, source_name):
                continue
            
            # Gov sources in RSS? Unlikely for ST/CNA but good practice
            is_gov = ".gov.sg" in link

            if not is_relevant_business_news(full_text, is_gov):
                continue
            
            # Adaptive Negative Filtering
            if vector_engine.is_similar_to_removed(full_text):
                print(f"Skipping (Content Filter): {title}")
                continue
                
            sector = classify_sector(full_text)
            agency = extract_agency(full_text)
            
            # Check for circular
            is_circular = "circular" in full_text.lower()
            
            # Impact
            impact = scorer.analyze_impact(title, summary_text)

            item = NewsItem(
                title=title,
                summary=summary_text,
                url=link,
                source=source_name,
                sector=classify_sector(title + " " + summary_text),
                agency=extract_agency(title + " " + summary_text, link),
                published_at=pub_date,
                is_circular="circular" in title.lower() or "circular" in link.lower(),
                impact_rating=impact
            )
            items.append(item)
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    return items

def fetch_gov_sg() -> List[NewsItem]:
    return [] # Disabled per user request

def fetch_history_backfill() -> List[NewsItem]:
    """Scans last 30 days for major sources using Google News proxy (Multi-Query Strategy)"""
    print("Backfilling 30-day history for whitelist sources...")
    all_items = []
    seen_urls = set()
    
    # Split queries to overcome RSS limits and ensure topic coverage
    site_list = "site:straitstimes.com OR site:channelnewsasia.com OR site:businesstimes.com.sg OR site:theedgesingapore.com"
    
    # Dynamic Query Builder
    queries = [
        # 1. General Regulatory
        f"({site_list}) (regulation OR policy OR rule OR law OR bill OR 'new requirement') when:30d",
        # 2. Key Agencies (Broad)
        f"({site_list}) (SFA OR MOM OR URA OR BCA OR MAS OR LTA OR MOH OR MUIS OR 'Enterprise Singapore') when:30d",
    ]

    # Dynamically build sector queries using rich KEYWORD_MAP
    # Group sectors into batches of ~4 to avoid URL length limits
    sector_batches = [ITM_SECTORS[i:i + 4] for i in range(0, len(ITM_SECTORS), 4)]
    
    for batch in sector_batches:
        batch_keywords = []
        for sector in batch:
            # Add Sector Name
            batch_keywords.append(f"'{sector}'")
            # Add top 3 synonyms/keywords for this sector
            if sector in KEYWORD_MAP:
                for kw in KEYWORD_MAP[sector][:3]: # Limit to top 3 to keep query length safe
                    if " " in kw:
                        batch_keywords.append(f"'{kw}'")
                    else:
                        batch_keywords.append(kw)
        
        # Construct query: (site...) AND (Sector1 OR Kw1 OR Sector2 OR Kw2...)
        joined_kws = " OR ".join(batch_keywords)
        query = f"({site_list}) ({joined_kws}) when:30d"
        queries.append(query)

    for q_idx, query in enumerate(queries):
        print(f"  -> Running Backfill Query {q_idx+1}...")
        encoded_query = requests.utils.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-SG&gl=SG&ceid=SG:en"
        
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:60]: # Fetch up to 60 per query
                link = entry.link
                if link in seen_urls:
                    continue
                seen_urls.add(link)

                title = entry.title
                
                # Clean title
                source_guess = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source_guess = parts[1]
                
                summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                soup = BeautifulSoup(summary, 'lxml')
                summary_text = soup.get_text()[:300] + "..."
                
                # Robust Date Parsing
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                elif hasattr(entry, 'published'):
                    try: pub_date = date_parser.parse(entry.published)
                    except: pass
                elif hasattr(entry, 'updated'):
                    try: pub_date = date_parser.parse(entry.updated)
                    except: pass
                
                if not pub_date:
                    # print(f"  [DATE WARNING] Could not parse date for '{title}'. Defaulting to NOW.")
                    pub_date = datetime.utcnow()
                    
                full_text = title + " " + summary_text + " " + source_guess
                
                # Filter: 30 days window
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                if pub_date < cutoff_date:
                    continue
                
                if "MyCareersFuture" in source_guess or "MyCareersFuture" in title:
                     continue

                # Strict Domain Whitelist check
                if not is_allowed_source(link, source_name=source_guess):
                    continue
                
                is_gov = ".gov.sg" in link or "gov.sg" in source_guess
                if not is_relevant_business_news(full_text, is_gov):
                    continue
                
                # Adaptive Negative Filtering
                if vector_engine.is_similar_to_removed(full_text):
                    continue

                sector = classify_sector(full_text)
                agency = extract_agency(full_text)
                is_circular = "circular" in full_text.lower()
                
                item = NewsItem(
                    title=title,
                    summary=summary_text,
                    url=link,
                    source=source_guess,
                    sector=sector,
                    agency=agency,
                    published_at=pub_date,
                    is_circular=is_circular
                )
                all_items.append(item)
        except Exception as e:
            print(f"Error fetching backfill query {q_idx}: {e}")
            
    return all_items

# Removed generate_fake_gov_sg to avoid broken links and hallucinations

def fetch_personalized_news() -> List[NewsItem]:
    """Fetches news based on top User Interests."""
    print("Fetching Personalized News based on User Interests...")
    items = []
    
    interests = []
    with Session(engine) as session:
        # Get Top 5 interests by score
        interests = session.exec(select(UserInterest).order_by(UserInterest.score.desc()).limit(5)).all()
        
    if not interests:
        print("No user interests found yet.")
        return []
        
    print(f"Top Interests: {[i.keyword for i in interests]}")
    
    # Construct queries
    # To save time, we can group them or run parallel, let's run sequential for now (limit 5)
    site_list = "site:straitstimes.com OR site:channelnewsasia.com OR site:businesstimes.com.sg"
    
    for interest in interests:
        try:
            query = f"({interest.keyword}) ({site_list}) when:30d"
            encoded_query = requests.utils.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-SG&gl=SG&ceid=SG:en"
            
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Top 5 per interest
                title = entry.title
                link = entry.link
                 # Deduplication handled by DB constraint later, but let's check basic
                
                summary = getattr(entry, 'summary', '')
                soup = BeautifulSoup(summary, 'lxml')
                summary_text = soup.get_text().strip()[:200]
                
                # Date
                pub_date = datetime.utcnow()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                full_text = title + " " + summary_text
                
                # Relaxed relevance for personalized (User explicitly wants this)
                # But still filter pure junk
                if "lottery" in full_text.lower() or "4d" in full_text.lower(): continue

                # Adaptive Negative Filtering (Crucial for learning what NOT to show even in interests)
                if vector_engine.is_similar_to_removed(full_text):
                    print(f"Skipping Interest Item (Content Filter): {title}")
                    continue

                item = NewsItem(
                    title=title,
                    summary=summary_text,
                    url=link,
                    source="Smart Interest", # Mark source for visibility or debugging? Or keep original? 
                    # Let's keep original source name if we can parse it, else "Google News (Interest)"
                    sector=classify_sector(full_text),
                    agency=extract_agency(full_text),
                    published_at=pub_date,
                    impact_rating=scorer.analyze_impact(title, summary_text)
                )
                # Parse source from title "Title - Source"
                if " - " in title:
                    item.source = title.rsplit(" - ", 1)[1]
                    item.title = title.rsplit(" - ", 1)[0]
                    
                items.append(item)
        except Exception as e:
            print(f"Error fetching interest '{interest.keyword}': {e}")
            
    return items

def fetch_news() -> List[NewsItem]:
    # Pre-load rejected vector cache
    vector_engine.load_rejected_embeddings()
    all_news = []
    
    # 1. Real RSS
    all_news.extend(fetch_rss_news("The Straits Times", RSS_FEEDS["The Straits Times"]))
    all_news.extend(fetch_rss_news("The Straits Times", RSS_FEEDS["The Straits Times (SG)"]))
    all_news.extend(fetch_rss_news("CNA", RSS_FEEDS["CNA"]))
    all_news.extend(fetch_rss_news("CNA", RSS_FEEDS["CNA (SG)"]))
    
    # 2. Business Times (Try RSS if valid, else skip)
    # bt_news = fetch_rss_news("The Business Times", "https://www.businesstimes.com.sg/rss.xml")
    # all_news.extend(bt_news)
    
    # 3. Gov.sg (Hybrid)
    all_news.extend(fetch_gov_sg())

    # 4. Personalised / Smart Interests
    all_news.extend(fetch_personalized_news())

    # 4. Backfill History (Straits Times, CNA, etc. - last 30 days)
    all_news.extend(fetch_history_backfill())
    
    return all_news

# Intelligent Search Expansion
SYNONYM_MAP = {
    "autonomous": ["self-driving", "driverless", "automated", "av"],
    "ev": ["electric vehicle", "charging", "clean energy"],
    "ai": ["artificial intelligence", "genai", "llm", "machine learning"],
    "green": ["sustainability", "carbon", "emission", "esg", "climate"],
    "cybersecurity": ["cyber", "data breach", "ransomware", "scam"],
    "fintech": ["digital bank", "payment", "crypto", "blockchain"],
    "manpower": ["labor", "workforce", "talent", "retrenchment", "hiring"],
    "sme": ["small business", "enterprise", "digitalisation", "grant"],
    "halal": ["muis", "muslim", "certification", "food safety"],
    "property": ["real estate", "housing", "ura", "hdb", "absd"],
}

def generate_search_summary(items: List[NewsItem], query: str) -> str:
    """Synthesizes a short 'AI' summary of the search results."""
    if not items:
        return f"No specific regulatory updates found for '{query}'."
    
    count = len(items)
    agencies = set(item.agency for item in items if item.agency and item.agency != "Unknown")
    sectors = set(item.sector for item in items if item.sector)
    
    # Find top recurring words in titles for "Key Themes"
    all_text = " ".join([item.title for item in items]).lower()
    themes = []
    potential_themes = ["launch", "grant", "fine", "ban", "framework", "roadmap", "safety", "standard", "license", "permit"]
    for theme in potential_themes:
        if theme in all_text:
            themes.append(theme.capitalize())
            
    summary = f"Found {count} articles relevant to '**{query}**'."
    
    if agencies:
        top_agencies = ", ".join(sorted(list(agencies))[:3])
        summary += f" Key updates involve **{top_agencies}**."
        
    if themes:
        summary += f" Major themes include **{', '.join(themes[:3])}**."
        
    return summary

def search_news(user_query: str) -> Dict:
    print(f"Searching for: {user_query}")
    items = []
    
    # Intelligent Query Pre-processing
    # remove stopwords to help Google News (which prefers keywords)
    stopwords = ["at", "on", "in", "to", "for", "of", "the", "a", "an", "and", "or", "speech"]
    clean_terms = [w for w in user_query.split() if w.lower() not in stopwords]
    cleaned_query = " ".join(clean_terms)
    
    # Use cleaned query for expansion if original is too long/complex
    base_query = cleaned_query if len(clean_terms) > 0 else user_query

    # 1. Intelligent Query Expansion
    expanded_terms = [base_query]
    query_lower = user_query.lower() # Check original for context keys
    for key, synonyms in SYNONYM_MAP.items():
        if key in query_lower:
            expanded_terms.extend(synonyms)
            
    # Join with OR, but keep original specific
    if len(expanded_terms) > 1:
        synonym_group = " OR ".join([f"'{t}'" for t in expanded_terms[1:4]])
        final_query = f"{base_query} OR ({synonym_group})"
    else:
        final_query = base_query

    # Construct query with site restrictions
    # Added site:.gov.sg per user request for MTI speeches/press releases
    sites = " OR ".join([f"site:{s}" if "site" not in s else s for s in ["straitstimes.com", "channelnewsasia.com", "businesstimes.com.sg", "theedgesingapore.com", ".gov.sg"]])
    # User Request: Manual Search should be dated/flexible (Exception to 30d rule)
    full_query = f"({final_query}) ({sites})"
    
    # Encode
    encoded_query = requests.utils.quote(full_query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-SG&gl=SG&ceid=SG:en"
    
    # print(f"DEBUG: Search URL: {url}")
    
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:20]: # Fetch up to 20 for search
            title = entry.title
            
            # Clean title
            source_guess = "Google News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0]
                source_guess = parts[1]

            link = entry.link
            
            summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            soup = BeautifulSoup(summary, 'lxml')
            summary_text = soup.get_text()[:300] + "..."
            
            # Robust Date Parsing with Debugging
            pub_date = None
            print(f"DEBUG_DATE: Title='{title}'")
            print(f"  Raw Published: {getattr(entry, 'published', 'N/A')}")
            print(f"  Raw Updated: {getattr(entry, 'updated', 'N/A')}")
            
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                print(f"  -> Used published_parsed: {pub_date}")
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                print(f"  -> Used updated_parsed: {pub_date}")
            elif hasattr(entry, 'published'):
                try: 
                    pub_date = date_parser.parse(entry.published)
                    print(f"  -> Parsed string published: {pub_date}")
                except Exception as e: print(f"  -> Failed parse published: {e}")
            elif hasattr(entry, 'updated'):
                try: 
                    pub_date = date_parser.parse(entry.updated)
                    print(f"  -> Parsed string updated: {pub_date}")
                except Exception as e: print(f"  -> Failed parse updated: {e}")
            
            if not pub_date:
                print(f"  -> RSS Date missing. Attempting Deep Scan...")
                # Use current entry.link which is Google redirect, requests will follow it
                pub_date = fetch_actual_date_from_url(link)
                
            if not pub_date:
                print(f"  -> Deep Scan Failed. Defaulting to NOW.")
                pub_date = datetime.utcnow()
            
            full_text = title + " " + summary_text + " " + source_guess
            
            sector = classify_sector(full_text)
            agency = extract_agency(full_text)
            is_circular = "circular" in full_text.lower()

            item = NewsItem(
                title=title,
                summary=summary_text,
                url=link,
                source=source_guess,
                sector=sector,
                agency=agency,
                published_at=pub_date,
                is_circular=is_circular
            )
            items.append(item)
            
    except Exception as e:
        print(f"Error searching: {e}")

    # Strategy Upgrade: ALWAYS try Key Entity Search if the query is complex (> 4 words)
    
    # Improved Extraction Logic: Handle lowercase inputs by aggressively stripping stopwords
    stopwords_entity = {
        "at", "on", "in", "to", "for", "of", "the", "a", "an", "and", "or", "is", "are", "with", "by", "from",
        "speech", "statement", "press", "release", "news", "update", "report", "media",
        "minister", "ministry", "dpm", "pm", "secretary", "government", "govt",
        "regulations", "regulation", "act", "bill", "law", "policy", "guidelines", "framework", "rules",
        "singapore", "sg", "new", "latest", "today", "regarding", "concerning", "about"
    }
    
    tokens = user_query.lower().split()
    fallback_tokens = []
    
    for t in tokens:
        t_clean = t.strip(".,()[]{}'\"")
        # Keep digits (2025) and non-stopword words > 1 char
        if t_clean and t_clean not in stopwords_entity and len(t_clean) > 1:
            fallback_tokens.append(t_clean)
    
    # Run "Smart Entity Search" if we have tokens AND the original query was complex
    should_run_smart = len(fallback_tokens) >= 1 and len(tokens) > 4
    
    if should_run_smart:
        fallback_query = " ".join(fallback_tokens)
        print(f"Smart Keyword Query: {fallback_query}")
        
        # Try Smart Search with Site Restrictions first
        # Manual Search Exception: No date limit
        fb_encoded = requests.utils.quote(f"({fallback_query}) ({sites})")
        fb_url = f"https://news.google.com/rss/search?q={fb_encoded}&hl=en-SG&gl=SG&ceid=SG:en"
        
        found_smart_items = []

        def fetch_smart_items(url_to_fetch, label="Restricted"):
            try:
                feed = feedparser.parse(url_to_fetch)
                for entry in feed.entries[:10]: 
                    title = entry.title
                    # Ignore generic "Newsroom" or "Home" titles
                    if title.strip() in ["Newsroom", "Home", "Media Releases"]:
                        continue

                    source_guess = "Google News"
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        title = parts[0]
                        source_guess = parts[1]
                    
                    full_text = title + " " + getattr(entry, 'summary', '')
                    
                    # Deduplicate
                    if any(i.url == entry.link for i in items): continue
                    if any(title.lower() in i.title.lower() or i.title.lower() in title.lower() for i in items): continue

                    sector = classify_sector(full_text)
                    agency = extract_agency(full_text)
                    
                    item = NewsItem(
                        title=title,
                        summary=entry.summary if hasattr(entry, 'summary') else title,
                        url=entry.link,
                        source=source_guess,
                        sector=sector,
                        agency=agency,
                        published_at=datetime.utcnow(), 
                        is_circular=False
                    )
                    items.append(item)
                    found_smart_items.append(item)
                    print(f"  -> Added Smart Result ({label}): {title}")
            except Exception as e:
                print(f"Smart Search ({label}) error: {e}")

        # 1. Restricted Search (High Precision, Low Recall for deep links)
        fetch_smart_items(fb_url, "Restricted")
        
        # 2. Global SG Search (High Recall, risk of noise)
        # ALWAYS run this to catch deep gov.sg links that Restricted Search misses (e.g. MTI Speech)
        print("  Running Global SG Search for fallback...")
        
        # Manual Search Exception: No date limit
        fb_encoded_global = requests.utils.quote(fallback_query)
        fb_url_global = f"https://news.google.com/rss/search?q={fb_encoded_global}&hl=en-SG&gl=SG&ceid=SG:en"
        
        # We need to be careful with Global results. 
        # Strategy: Fetch them, but prioritize SG content.
        try:
            feed = feedparser.parse(fb_url_global)
            for entry in feed.entries[:15]: # Expanded to 15 to catch MTI if ranked lower
                title = entry.title
                if title.strip() in ["Newsroom", "Home", "Media Releases"]: continue

                source_guess = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source_guess = parts[1]
                
                # Global Filter: Prefer SG domains or known entities
                # Note: "entry.link" is often a Google redirect (news.google.com/...), so .sg check usually fails there.
                # We rely on Source Guess and Title.
                
                is_sg_likely = False
                
                # Agency / Source Keywords
                sg_source_keywords = ["Ministry", "Authority", "Board", "Council", "Agency", "Commission", "Straits Times", "CNA", "Business Times", "Today", "Edge Singapore", "Gov.sg"]
                if any(k.lower() in source_guess.lower() for k in sg_source_keywords):
                    is_sg_likely = True
                
                # Location Keywords in Source or Title
                if "Singapore" in title or "Singapore" in source_guess:
                    is_sg_likely = True
                    
                # Specific overrides for user queries (e.g. PEP Awards is strictly SG logic usually? No, global.)
                # If source ends with .sg in display name (rare)
                
                # If not clearly SG, skip it (filters Jamaica/Man City)
                if not is_sg_likely:
                    continue

                full_text = title + " " + getattr(entry, 'summary', '')
                
                # Deduplicate
                if any(i.url == entry.link for i in items): continue
                if any(title.lower() in i.title.lower() or i.title.lower() in title.lower() for i in items): continue

                sector = classify_sector(full_text)
                agency = extract_agency(full_text)
                
                # Robust Date Parsing
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                elif hasattr(entry, 'published'):
                     try: pub_date = date_parser.parse(entry.published)
                     except: pass
                
                if not pub_date:
                     print(f"  -> Global Fallback Date missing. Deep Scan...")
                     pub_date = fetch_actual_date_from_url(entry.link)
                     
                if not pub_date:
                     pub_date = datetime.utcnow()

                item = NewsItem(
                    title=title,
                    summary=entry.summary if hasattr(entry, 'summary') else title,
                    url=entry.link,
                    source=source_guess,
                    sector=sector,
                    agency=agency,
                    published_at=pub_date, 
                    is_circular=False
                )
                items.append(item)
                print(f"  -> Added Smart Global Result: {title}")
        except Exception as e:
            print(f"Smart Global error: {e}")

    # Re-Ranking Logic: Prioritize Relevance over Source Order
    # 1. Exact Title Match for Fallback Keywords (e.g. "PEP Awards")
    # 2. Official Government Sources
    # 3. Penalize Generic Titles
    
    def get_search_rank(item):
        score = 0
        title_lower = item.title.lower()
        
        # Keyword Match
        if fallback_tokens:
             matches = sum(1 for t in fallback_tokens if t.lower() in title_lower)
             if matches == len(fallback_tokens):
                 score += 50
             elif matches > 0:
                 score += 10 * matches
        
        # Source Boost
        if "ministry" in item.source.lower() or "authority" in item.source.lower() or "gov.sg" in item.url:
            score += 30
            
        # Generic Penalty
        if item.title.strip() in ["Newsroom", "Home", "Media Releases", "Press Releases"]:
            score -= 100
            
        return score

    # Sort mainly by Relevance Score, secondarily by date (if available)
    items.sort(key=lambda x: get_search_rank(x), reverse=True)

    # Generate AI Summary
    ai_summary = generate_search_summary(items, user_query)

    return {
        "summary": ai_summary,
        "items": items
    }
