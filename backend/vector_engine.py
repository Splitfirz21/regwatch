"""
Lightweight Vector Engine Replacement for Free Tier Cloud Deployment.
Removes 'sentence-transformers' and 'torch' dependencies to save ~500MB RAM.
Falls back to simple keyword matching.
"""
from typing import List
from models import NewsItem

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

def search_similar(query: str, items: List[NewsItem], top_k: int = 5) -> List[NewsItem]:
    """
    Find items similar to query using simple keyword matching.
    Memory Usage: Minimal.
    """
    if not items or not query:
        return []
    
    query_terms = set(query.lower().split())
    
    results = []
    for item in items:
        # Simple scoring: count overlapping words in title
        # We focus on Title relevance for speed
        text = (item.title + " " + (item.summary or "")).lower()
        score = 0
        for term in query_terms:
            if term in text:
                score += 1
        
        # Boost if precise phrase match in title
        if query.lower() in item.title.lower():
            score += 5
            
        if score > 0:
            results.append((score, item))
            
    # Sort by score desc, return top_k
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:top_k]]

def is_similar_to_removed(text: str, threshold: float = 0.85) -> bool:
    """
    Stub: Negative filtering disabled in Lite Mode to save resources.
    We could implement text-based filtering but it's risky (false positives).
    """
    return False
