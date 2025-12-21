"""
Lightweight Vector Engine Replacement for Free Tier Cloud Deployment.
Supports:
1. Level 3: Semantic Search (Remote Embeddings via Gemini + PGVector)
2. Level 2: Smart Search (Postgres FTS)
3. Level 1: Keyword Match (Fallback)
"""
from typing import List, Optional
from models import NewsItem
from sqlmodel import Session, select, text
import os
import google.generativeai as genai

IS_LITE = True

def get_model():
    # Model is remote (Gemini)
    return True

def index_items(items: List[NewsItem]):
    # Items are indexed specific backfill scripts or hook
    pass

def load_rejected_embeddings():
    pass

def get_remote_embedding(text: str) -> Optional[List[float]]:
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        # Model: embedding-001 (768 dims, standard)
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_query" 
        )
        return result['embedding']
    except Exception as e:
        print(f"Embedding Gen Failed: {e}")
        return None

def search_similar(query: str, items: Optional[List[NewsItem]] = None, top_k: int = 5, session: Optional[Session] = None) -> List[NewsItem]:
    """
    Smart Search Strategy:
    1. Try Remote Semantic Search (Best)
    2. Try Postgres FTS (Good)
    3. Try Keyword (Basic)
    """
    if not query:
        return []
        
    if session:
        # STRATEGY 1: Remote Semantic Search (Vector)
        # Requires GOOGLE_API_KEY and pgvector setup
        query_vec = get_remote_embedding(query)
        if query_vec:
            try:
                # Cosine Distance: <=>
                # Using raw SQL for vector operations
                sql = text('''
                    SELECT * FROM newsitem 
                    WHERE is_hidden = False
                    ORDER BY embedding <=> :current_embedding
                    LIMIT :limit
                ''')
                
                # Pass list as string representation '[0.1, ...]' for safer raw SQL binding
                vec_str = str(query_vec)
                results = session.exec(sql, params={"current_embedding": vec_str, "limit": top_k}).all()
                items_mapped = [NewsItem(**dict(row._mapping)) for row in results]
                if items_mapped:
                    return items_mapped
            except Exception as e:
                # print(f"Vector search failed (maybe no extension?): {e}")
                pass

        # STRATEGY 2: Postgres Full Text Search (FTS)
        try:
            sql = text('''
                SELECT * FROM newsitem 
                WHERE is_hidden = False
                AND to_tsvector('english', title || ' ' || COALESCE(summary, '')) @@ websearch_to_tsquery('english', :q)
                ORDER BY ts_rank(to_tsvector('english', title || ' ' || COALESCE(summary, '')), websearch_to_tsquery('english', :q)) DESC
                LIMIT :limit
            ''')
            results = session.exec(sql, params={"q": query, "limit": top_k}).all()
            items_mapped = [NewsItem(**dict(row._mapping)) for row in results]
            if items_mapped:
                 return items_mapped
        except Exception:
             pass
             
        # STRATEGY 3: ILIKE
        try:
            statement = select(NewsItem).where(NewsItem.is_hidden == False)
            terms = query.split()
            for term in terms:
                statement = statement.where(NewsItem.title.ilike(f"%{term}%"))
            results = session.exec(statement.limit(top_k)).all()
            if results:
                return results
        except Exception:
            pass

    # Fallback In-Memory (If no session passed)
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
