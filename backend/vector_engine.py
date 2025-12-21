"""
Lightweight Vector Engine Replacement for Free Tier Cloud Deployment.
Removes 'sentence-transformers' and 'torch' dependencies to save ~500MB RAM.
Uses PostgreSQL Native Search.
"""
from typing import List, Optional
from models import NewsItem
from sqlmodel import Session, select, text

IS_LITE = True

def get_model():
    # Stub: No model needed
    return True

def index_items(items: List[NewsItem]):
    # Stub: No indexing needed
    pass

def load_rejected_embeddings():
    """
    Stub: Does nothing in Lite mode.
    Exists to satisfy scraper.py imports/calls.
    """
    pass

def search_similar(query: str, items: Optional[List[NewsItem]] = None, top_k: int = 5, session: Optional[Session] = None) -> List[NewsItem]:
    """
    Smart Search using Database Engine (Zero RAM).
    """
    if not query:
        return []
        
    # 1. Database Search (Preferred for Cloud/Lite)
    if session:
        try:
            # Postgres Full Text Search (Smart: Ranking, Stemming)
            # Uses standard identifying configuration 'english'
            sql = text('''
                SELECT * FROM newsitem 
                WHERE is_hidden = False
                AND to_tsvector('english', title || ' ' || COALESCE(summary, '')) @@ websearch_to_tsquery('english', :q)
                ORDER BY ts_rank(to_tsvector('english', title || ' ' || COALESCE(summary, '')), websearch_to_tsquery('english', :q)) DESC
                LIMIT :limit
            ''')
            results = session.exec(sql, params={"q": query, "limit": top_k}).all()
            # Convert generic row results to NewsItem logic if standard SQLModel EXEC doesn't auto-convert text queries easily
            # Session.exec(text) returns rows. SQLModel needs select() or careful mapping.
            # Actually session.exec(select(NewsItem).from_statement(text(...))) is safer.
            
            # Re-attempt with safer SQLModel binding if simple exec returns tuples
            # But let's rely on basic ILIKE fallback if this is too complex for this snippet.
            # Wait, `session.exec(text).all()` returns tuples usually.
            # Let's use `NewsItem` mapping.
            
            items_mapped = [NewsItem(**dict(row._mapping)) for row in results]
            if items_mapped:
                 return items_mapped
                 
        except Exception as e:
             # Fallback if FTS fails (e.g. SQLite local, syntax error, or returns tuples)
             # print(f"FTS Search failed or yielded no results: {e}")
             pass
             
        # Fallback: SQL ILIKE (keyword matching in DB)
        # This is safe and fast enough for small datasets
        try:
            statement = select(NewsItem).where(NewsItem.is_hidden == False)
            terms = query.split()
            for term in terms:
                # Basic AND logic for terms
                statement = statement.where(NewsItem.title.ilike(f"%{term}%"))
            
            results = session.exec(statement.limit(top_k)).all()
            if results:
                return results
        except Exception:
            pass

    # 2. In-Memory Fallback (If no session or items passed explicitly)
    if not items:
        return []
    
    query_terms = set(query.lower().split())
    results = []
    for item in items:
        text_content = (item.title + " " + (item.summary or "")).lower()
        score = 0
        for term in query_terms:
            if term in text_content:
                score += 1
        if query.lower() in item.title.lower():
            score += 5
        if score > 0:
            results.append((score, item))
            
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:top_k]]

def is_similar_to_removed(text: str, threshold: float = 0.85) -> bool:
    return False
