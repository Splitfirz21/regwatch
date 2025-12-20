from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlmodel import Session, select, func
from typing import List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import pandas as pd
import io

from database import create_db_and_tables, get_session, engine as db_engine
from models import NewsItem, Feedback, UserInterest
from dateutil import parser as date_parser
import scorer # Impact logiced from 'from scraper import fetch_news, search_news' to 'import scraper'
import scraper
from engine import engine as relevance_engine
import vector_engine # RAG

# Scheduler setup
scheduler = BackgroundScheduler()

from difflib import SequenceMatcher

def scheduled_scrape():
    print("Running scheduled scrape...")
    headers = {"User-Agent": "Mozilla/5.0"}
    items = scraper.fetch_news()
    
    with Session(db_engine) as session:
        existing_db_items = session.exec(select(NewsItem)).all()
        url_map = {item.url: item for item in existing_db_items}
        existing_titles = [(item.title, item) for item in existing_db_items]
        
        new_count = 0
        updated_count = 0
        
        for item in items:
            # 1. URL Check (Exact Match)
            if item.url in url_map:
                existing = url_map[item.url]
                if not existing.is_manual and item.impact_rating != existing.impact_rating: 
                     existing.impact_rating = item.impact_rating
                     session.add(existing)
                     updated_count += 1
                continue

            # 2. Fuzzy Title Check
            matched_existing = None
            normalized_new = item.title.lower()
            
            for ex_title, ex_item in existing_titles:
                # Check similarity
                ratio = SequenceMatcher(None, normalized_new, ex_title.lower()).ratio()
                if ratio > 0.65: # Similarity Threshold
                    matched_existing = ex_item
                    print(f"Fuzzy Match: '{item.title}' matches '{ex_title}' ({ratio:.2f}). Merging Sources.")
                    break
            
            if matched_existing:
                # Merge Logic
                if matched_existing.related_sources is None:
                    matched_existing.related_sources = []
                    
                existing_urls = {s.get('url') for s in matched_existing.related_sources}
                existing_urls.add(matched_existing.url) # Also verify against the primary URL
                
                if item.url not in existing_urls:
                    new_sources = list(matched_existing.related_sources)
                    new_sources.append({
                        "source": item.source,
                        "url": item.url,
                        "date": item.published_at.isoformat() if item.published_at else None
                    })
                    matched_existing.related_sources = new_sources
                    session.add(matched_existing)
                    updated_count += 1
            else:
                # Add new item
                session.add(item)
                url_map[item.url] = item 
                existing_titles.append((item.title, item))
                new_count += 1
        
        session.commit()
    print(f"Scraped {len(items)} items. Added {new_count}, Updated {updated_count}.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Schedule every hour
    scheduler.add_job(scheduled_scrape, 'interval', hours=1)
    scheduler.start()
    # scheduled_scrape() # Disable auto-run on boot to prevent crash loop
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(scheduled_scrape)
    return {"message": "Scan triggered in background"}

class UpdateItemRequest(BaseModel):
    sector: Optional[str] = None
    agency: Optional[str] = None
    impact_rating: Optional[str] = None # Support manual impact reclassification

@app.patch("/items/{item_id}")
def update_item(item_id: int, update: UpdateItemRequest, session: Session = Depends(get_session)):
    item = session.get(NewsItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update fields if provided
    if update.sector is not None:
        item.sector = update.sector
    if update.agency is not None:
        item.agency = update.agency
    if update.impact_rating is not None:
        # TODO: Implement "Learning" from this override (User Request)
        # For now, just apply the override.
        # Check against heuristics? No, user overrides everything.
        print(f"Manual Impact Override: {item.title} ({item.impact_rating} -> {update.impact_rating})")
        item.impact_rating = update.impact_rating
        
    # Mark as manually corrected so scanner doesn't overwrite
    item.is_manual = True
    
    session.add(item)
    session.commit()
    session.refresh(item)
    session.refresh(item)
    return item

@app.post("/items", response_model=NewsItem)
def create_item(item: NewsItem, session: Session = Depends(get_session)):
    print(f"DEBUG: create_item payload: {item}")
    # Check for existing URL to avoid duplicates
    existing = session.exec(select(NewsItem).where(NewsItem.url == item.url)).first()
    if existing:
        # If it was hidden, unhide it?
        if existing.is_hidden:
            existing.is_hidden = False
            session.add(existing)
            session.commit()
            session.refresh(existing)
        return existing
        
    # Ensure fresh ID
    item.id = None

    # Fix SQLite DateTime type error if Pydantic passed string
    if isinstance(item.published_at, str):
        try:
            # Try ISO format first
            item.published_at = datetime.fromisoformat(item.published_at.replace('Z', '+00:00'))
        except:
            try:
                # Try DateUtil for other formats (Fri, 21 Nov ...)
                item.published_at = date_parser.parse(item.published_at)
            except Exception as e:
                print(f"DEBUG: Failed to parse published_at '{item.published_at}': {e}. Defaulting to NOW.")
                item.published_at = datetime.utcnow()

    if item.scraped_at and isinstance(item.scraped_at, str):
        try:
            item.scraped_at = datetime.fromisoformat(item.scraped_at.replace('Z', '+00:00'))
        except:
            item.scraped_at = datetime.utcnow()
        
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.get("/news", response_model=List[NewsItem])
def get_news(sector: Optional[str] = None, limit: Optional[int] = None, offset: int = 0, session: Session = Depends(get_session)):
    try:
        # Filter hidden items
        query = select(NewsItem).where(NewsItem.is_hidden == False)
        if sector:
            query = query.where(NewsItem.sector == sector)
            
        # Sort
        query = query.order_by(NewsItem.published_at.desc())
        
        # Apply pagination only if requested
        if limit:
            query = query.limit(limit).offset(offset)
            
        items = session.exec(query).all()
        return items
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

@app.post("/feedback")
def submit_feedback(feedback: Feedback, session: Session = Depends(get_session)):
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return {"status": "ok"}

@app.delete("/items/{item_id}")
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(NewsItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Soft delete (hide) instead of removing record
    item.is_hidden = True
    session.add(item)
    session.commit()
    return {"status": "hidden"}

@app.post("/items/{item_id}/toggle-save")
def toggle_save_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(NewsItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.is_saved = not item.is_saved
    session.add(item)
    
    # Capture Interest if Saved
    if item.is_saved:
        try:
            # Heuristic: Use Sector + Agency + Top Keywords?
            # Let's use the explicit tags first as they are cleanest
            terms = []
            if item.sector and item.sector != "General": terms.append(item.sector)
            if item.agency and item.agency != "Unknown": 
                # Split agency "LTA, MOT" -> ["LTA", "MOT"]
                terms.extend([a.strip() for a in item.agency.split(',')])
            
            # Upsert
            for term in terms:
                term_key = term.lower()
                existing = session.get(UserInterest, term_key)
                if existing:
                    existing.score += 2.0 # Higher weight for saved items
                    existing.last_active = datetime.utcnow()
                    session.add(existing)
                else:
                    new_int = UserInterest(keyword=term_key, score=2.0, source="saved_item")
                    session.add(new_int)
            print(f"Captured Interest (Save): {terms}")
        except Exception as e:
            print(f"Failed to capture saved interest: {e}")

    session.commit()
    session.refresh(item)
    return {"status": "ok", "is_saved": item.is_saved}

@app.post("/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(scheduled_scrape)
    return {"message": "Scan triggered in background"}

@app.get("/export")
def export_news(session: Session = Depends(get_session)):
    """Exports all valid news items to an Excel file."""
    try:
        # Fetch data
        query = select(NewsItem).where(NewsItem.is_hidden == False).order_by(NewsItem.published_at.desc())
        items = session.exec(query).all()
        
        # Convert to DataFrame
        data = []
        for item in items:
            data.append({
                "Article Name": item.title,
                "Sector": item.sector,
                "Agency": item.agency,
                "URL": item.url,
                "Published Date": item.published_at.strftime("%Y-%m-%d %H:%M") if item.published_at else ""
            })
            
        df = pd.DataFrame(data)
        
        # Create Excel Buffer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Regulatory News')
            
        output.seek(0)
        
        headers = {
            'Content-Disposition': f'attachment; filename="regwatch_export_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        }
        
        return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except Exception as e:
        print(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats(impact: Optional[str] = None, session: Session = Depends(get_session)):
    try:
        query = select(NewsItem).where(NewsItem.is_hidden == False)
        if impact and impact != 'All':
            query = query.where(NewsItem.impact_rating == impact)
            
        items = session.exec(query).all()
        
        # Calculate stats
        total = len(items)
        
        # Impact Distribution
        impact_counts = {}
        for i in items:
            impact_counts[i.impact_rating] = impact_counts.get(i.impact_rating, 0) + 1
            
        impact_data = [{"name": k, "value": v} for k, v in impact_counts.items()]
        
        # Top Sectors
        sector_counts = {}
        for i in items:
            if i.sector:
                sector_counts[i.sector] = sector_counts.get(i.sector, 0) + 1
        sectors_data = [{"name": k, "value": v} for k, v in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        # Top Agencies
        agency_counts = {}
        for i in items:
            if i.agency:
                agency_counts[i.agency] = agency_counts.get(i.agency, 0) + 1
        agencies_data = [{"name": k, "value": v} for k, v in sorted(agency_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        return {
            "total": total,
            "impact": impact_data,
            "sectors": sectors_data,
            "agencies": agencies_data
        }
    except Exception as e:
        print(f"Stats check failed: {e}")
        return {
            "total": 0, "impact": [], "sectors": [], "agencies": []
        }

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    summary: str
    items: List[NewsItem]

@app.post("/search", response_model=SearchResponse)
def search_regulatory_scout(req: SearchRequest, session: Session = Depends(get_session)):
    # 1. Try Vector Search on Local DB first
    # Get all valid items
    db_items = session.exec(select(NewsItem).where(NewsItem.is_hidden == False)).all()
    
    # Search locally
    local_results = vector_engine.search_similar(req.query, list(db_items), top_k=5)
    
    # 2. Results Strategy
    # If we have good local results, use them.
    # Otherwise, go to Google News (Web).
    # For now, let's mix or prioritize local.
    
    found_items = []
    
    # Convert local results to list
    if local_results:
        found_items.extend(local_results)
        
    # If not enough, try Web Search (scraper)
    if len(found_items) < 5:
        print("Not enough local vector results, trying Web Search...")
        web_results_dict = scraper.search_news(req.query) # returns {summary, items}
        web_items = web_results_dict.get("items", [])
        
        # Deduplicate by URL
        existing_urls = {i.url for i in found_items}
        for w in web_items:
            if w.url not in existing_urls:
                found_items.append(w)
                
    # 3. Generate Summary (Simple Mock or Reuse Scraper's logic?)
    # scraper.search_news returns a summary generated by AI (if implemented there)
    # Here let's just use a placeholder or the one from web_results if available
    summary = "System found relevant articles."
    if 'web_results_dict' in locals() and web_results_dict.get("summary"):
        summary = web_results_dict["summary"]

    # 4. CAPTURE USER INTEREST (Smart Learning)
    try:
        # Simple extraction: just the raw query for now, or cleaned
        # We can rely on scraper's cleaning, but let's just save the raw query lowercased
        interest_term = req.query.lower().strip()
        if len(interest_term) > 3: # Ignore short junk
            existing_interest = session.get(UserInterest, interest_term)
            if existing_interest:
                existing_interest.score += 1.0
                existing_interest.last_active = datetime.utcnow()
                session.add(existing_interest)
            else:
                new_interest = UserInterest(keyword=interest_term, score=1.0, source="search")
                session.add(new_interest)
            session.commit()
            print(f"Captured Interest (Search): {interest_term}")
    except Exception as e:
        print(f"Failed to capture search interest: {e}")
        
    return SearchResponse(summary=summary, items=found_items[:10])

@app.post("/items")
def add_news_item(item: NewsItem, session: Session = Depends(get_session)):
    # Fix SQLite DateTime type error if Pydantic passed string
    if isinstance(item.published_at, str):
        try:
            # Try ISO format first
            item.published_at = datetime.fromisoformat(item.published_at.replace('Z', '+00:00'))
        except:
            try:
                # Try DateUtil for other formats (Fri, 21 Nov ...)
                item.published_at = date_parser.parse(item.published_at)
            except Exception as e:
                print(f"DEBUG: Failed to parse published_at '{item.published_at}': {e}. Defaulting to NOW.")
                item.published_at = datetime.utcnow()
            
    # Fix: Reset scraped_at to now (since we are adding it now) or parse it
    item.scraped_at = datetime.utcnow()

    # check for existence
    existing = session.exec(select(NewsItem).where(NewsItem.url == item.url)).first()
    if existing:
        # If it was hidden (soft deleted), un-hide it because user explicitly added it back
        if existing.is_hidden:
            existing.is_hidden = False
            session.add(existing)
            session.commit()
            return {"status": "restored", "id": existing.id}
        return {"status": "exists", "id": existing.id}
    
    session.add(item)
    
    # Capture Interest from Added Item (Smart Learning)
    try:
        # Heuristic: Use Sector + Agency
        terms = []
        if item.sector and item.sector != "General": terms.append(item.sector)
        if item.agency and item.agency != "Unknown": 
            terms.extend([a.strip() for a in item.agency.split(',')])
        
        # Upsert
        for term in terms:
            term_key = term.lower()
            existing = session.get(UserInterest, term_key)
            if existing:
                existing.score += 2.0 # High weight for manually added items
                existing.last_active = datetime.utcnow()
                session.add(existing)
            else:
                new_int = UserInterest(keyword=term_key, score=2.0, source="added_item")
                session.add(new_int)
        if terms:
            print(f"Captured Interest (Add): {terms}")
    except Exception as e:
        print(f"Failed to capture added interest: {e}")

    session.commit()
    session.refresh(item)
    return {"status": "added", "id": item.id}

@app.patch("/items/{item_id}")
def update_item(item_id: int, updates: dict, session: Session = Depends(get_session)):
    item = session.get(NewsItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    # Apply updates
    for key, value in updates.items():
        if hasattr(item, key):
            setattr(item, key, value)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.get("/stats")
def get_stats(impact: Optional[str] = None, session: Session = Depends(get_session)):
    """Aggregation stats for Dashboard. Optional filter by impact."""
    query = select(NewsItem).where(NewsItem.is_hidden == False)
    
    if impact and impact != "All":
        query = query.where(NewsItem.impact_rating == impact)
        
    items = session.exec(query).all()
    
    # Init counters
    sectors = {}
    agencies = {}
    impact_counts = {"High": 0, "Medium": 0, "Low": 0}
    
    for item in items:
        # Sector
        s = item.sector or "Unknown"
        sectors[s] = sectors.get(s, 0) + 1
        
        # Agency
        a = item.agency or "Unknown"
        agencies[a] = agencies.get(a, 0) + 1
        
        # Impact
        i = item.impact_rating or "Medium"
        impact_counts[i] = impact_counts.get(i, 0) + 1
        
    # Formatting for Recharts (List of Dicts)
    def to_chart_data(d):
        return [{"name": k, "value": v} for k, v in d.items()]
        
    return {
        "sectors": sorted(to_chart_data(sectors), key=lambda x: x['value'], reverse=True),
        "agencies": sorted(to_chart_data(agencies), key=lambda x: x['value'], reverse=True),
        "impact": to_chart_data(impact_counts),
        "total": len(items)
    }

class BriefRequest(BaseModel):
    impact: Optional[str] = None

@app.post("/brief")
def generate_brief(req: BriefRequest = None, session: Session = Depends(get_session)):
    """Generates an Executive Briefing Markdown using Google Gemini."""
    import google.generativeai as genai
    import os

    # Configure Gemini
    # In production, use os.environ['GEMINI_API_KEY']
    # For now, using the key provided by user (hardcoded for this session context)
    API_KEY = "AIzaSyCPKl16zeHd45v9vW0cPbEg8IK0oIusjIw"
    genai.configure(api_key=API_KEY)
    
    # Base query
    query = select(NewsItem).where(NewsItem.is_hidden == False)
    
    # Filter
    impact_filter = "High" # Default
    if req and req.impact and req.impact != "All":
        impact_filter = req.impact
        query = query.where(NewsItem.impact_rating == impact_filter)
    elif req and req.impact == "All":
         impact_filter = "All"
    else:
        query = query.where(NewsItem.impact_rating == "High")

    # Sort and Limit - Increased limit for LLM context
    query = query.order_by(NewsItem.published_at.desc()).limit(30)
    items = session.exec(query).all()
    
    date_str = datetime.now().strftime("%d %B %Y")
    filter_label = f"({impact_filter} Impact)" if impact_filter != "All" else "(All Updates)"
    
    if not items:
        return {"content": f"# 📋 Executive Regulatory Brief {filter_label}\n**Date**: {date_str}\n\nNo recent updates found for this criteria."}

    import requests
    
    llm_success = False
    md_content = ""
    
    # Try LLM First
    try:
        # Construct LLM Prompt
        prompt = f"""
        You are a Senior Regulatory Affairs Analyst in Singapore. 
        Write an Executive Briefing based on the following {len(items)} regulatory updates ({filter_label}).
        
        **Instructions**:
        1. **Executive Summary**: Synthesize the key themes and biggest risks/opportunities in 2-3 sentences.
        2. **Sector Breakdown**: Group updates logically by sector (e.g. Finance, Transport, Tech).
        3. **Tone**: Professional, concise, authoritative.
        4. **Format**: Markdown. Use emojis for sections but keep it professional.
        5. **Impact**: Highlight 'High Impact' items specifically.
        
        **News Items**:
        """
        for item in items:
            prompt += f"- [{item.impact_rating} Impact] [{item.agency}] {item.title}: {item.summary}\n"

        # Using REST API
        API_KEY = "AIzaSyAbZmtaS3zk2aURDr4jJ8ngm7u8oFX76yU"
        # Try gemini-pro (stable) which is most universally available
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
        
        headers = { "Content-Type": "application/json", "Referer": "http://localhost:3005/" }
        data = { "contents": [{ "parts": [{"text": prompt}] }] }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            json_res = response.json()
            md_content = json_res['candidates'][0]['content']['parts'][0]['text']
            llm_success = True
        else:
            print(f"Gemini API Error ({response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"LLM Connection Error: {e}")

    # Fallback to Heuristic if LLM failed
    if not llm_success:
        from collections import Counter
        import re
        
        md_content = f"# 📋 Executive Regulatory Brief {filter_label}\n**Date**: {date_str}\n"
        md_content += "> ⚠️ **Note**: AI summarization failed (API Key restrictions). Showing keyword synthesis instead.\n\n"
        
        text = " ".join([i.title for i in items]).lower()
        words = re.findall(r'\b[a-z]{3,}\b', text)
        stopwords = {'the', 'and', 'for', 'that', 'with', 'from', 'this', 'singapore', 'new', 'update', 'report'}
        filtered = [w for w in words if w not in stopwords]
        common = Counter(filtered).most_common(5)
        keywords = ", ".join([c[0].title() for c in common])
        
        md_content += "## 🤖 Auto-Synthesis\n"
        md_content += f"**Key Themes**: {keywords}\n\n"
        md_content += f"**Summary**: This brief covers **{len(items)}** recent updates. "
        
        if "tax" in keywords.lower(): md_content += "Notable activity in taxation. "
        if "digital" in keywords.lower(): md_content += "Focus on digital governance. "
        if "environment" in keywords.lower(): md_content += "Sustainability updates detected. "
        md_content += "\n\n---\n"
        
        # Group by Sector manually since LLM didn't do it
        by_sector = {}
        for item in items:
            s = item.sector or "General"
            if s not in by_sector: by_sector[s] = []
            by_sector[s].append(item)
            
        for sector, sector_items in by_sector.items():
            md_content += f"## {sector}\n"
            for item in sector_items:
                agency_tag = f"**[{item.agency}]** " if item.agency else ""
                impact_badge = ""
                if item.impact_rating == 'High': impact_badge = "🔴 "
                elif item.impact_rating == 'Medium': impact_badge = "🟠 "
                elif item.impact_rating == 'Low': impact_badge = "⚪ "
                md_content += f"- {impact_badge}{agency_tag}{item.title}\n  > *{item.summary}*\n\n"

    # Final cleanup
    if "# Executive" not in md_content:
        md_content = f"# 📋 Executive Regulatory Brief {filter_label}\n**Date**: {date_str}\n\n" + md_content

    md_content += "---\n*Generated by RegWatch AI*"
    return {"content": md_content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
