from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any
from models import NewsItem
from database import engine
from sqlmodel import Session, select

# Singleton to hold model
_model = None
_embeddings = None # List of (id, vector)
_ids = []

def get_model():
    global _model
    if _model is None:
        print("Loading Vector Model (all-MiniLM-L6-v2)...")
        try:
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Vector Model Loaded.")
        except Exception as e:
            print(f"Failed to load vector model: {e}")
            return None
    return _model

def index_items(items: List[NewsItem]):
    """Re-index all items based on title+summary."""
    global _embeddings, _ids
    model = get_model()
    if not model or not items:
        return

    print(f"Indexing {len(items)} items for vector search...")
    texts = [f"{item.title} {item.summary}" for item in items]
    
    # Generate embeddings
    embeddings = model.encode(texts, convert_to_numpy=True)
    
    # Store
    _embeddings = embeddings
    _ids = [item.id for item in items]
    print("Indexing Complete.")

def search_similar(query: str, items: List[NewsItem], top_k: int = 5) -> List[NewsItem]:
    """Find items similar to query."""
    global _embeddings, _ids
    model = get_model()
    if not model:
        return []

    # If index empty/stale, re-index instant (naive cache)
    # Ideally should be sync with DB but for demo, we index on scrape or startup?
    # For now, let's assume index_items is called.
    # If index empty/stale or counts mismatch (new items added), re-index
    # This ensures search results are always fresh
    if _embeddings is None or len(_embeddings) == 0 or len(_embeddings) != len(items):
        print("Vector Index Stale or Mismatch. Re-indexing...")
        index_items(items)
    
    if _embeddings is None or len(_embeddings) == 0:
        return []

    # Embed query
    query_vec = model.encode([query], convert_to_numpy=True)[0]
    
    # Cosine Similarity
    # (A . B) / (|A| * |B|)
    # Normalize vectors first for faster dot product
    # sentence-transformers output is usually normalized? No.
    from sklearn.metrics.pairwise import cosine_similarity
    
    scores = cosine_similarity([query_vec], _embeddings)[0]
    
    # Get Top K indices
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    results = []
    # Map back to items
    # We rely on items being list passed in, matching _ids order? 
    # Logic flaw: items passed in might be filtered.
    # Better: Use _ids to map to Item ID, then match with input list.
    
    id_map = {item.id: item for item in items}
    
    for idx in top_indices:
        score = scores[idx]
        item_id = _ids[idx]
        if score > 0.25: # Threshold
            if item_id in id_map:
                item = id_map[item_id]
                # Attach score for debugging if needed
                results.append(item)
    
    return results

# Negative Filtering Logic
_rejected_embeddings = None
_rejected_texts = []

def load_rejected_embeddings():
    """Loads removed (is_hidden=True) items and computes embeddings."""
    global _rejected_embeddings, _rejected_texts
    model = get_model()
    if not model: return

    with Session(engine) as session:
        # Get hidden items
        # Limit to recent 100 to avoid performance hit?
        # User wants "removed articles from dashboard", so is_hidden=True
        removed = session.exec(select(NewsItem).where(NewsItem.is_hidden == True)).all()
        
    if not removed:
        _rejected_embeddings = []
        _rejected_texts = []
        return

    print(f"Indexing {len(removed)} removed items for negative filtering...")
    texts = [f"{item.title} {item.summary}" for item in removed]
    _rejected_texts = texts
    
    # Compute
    _rejected_embeddings = model.encode(texts, convert_to_numpy=True)
    print("Negative Indexing Complete.")

def is_similar_to_removed(text: str, threshold: float = 0.85) -> bool:
    """Checks if text is semantically similar to any removed item."""
    global _rejected_embeddings
    
    # Lazy Load
    if _rejected_embeddings is None:
        load_rejected_embeddings()
        
    if _rejected_embeddings is None or len(_rejected_embeddings) == 0:
        return False
        
    model = get_model()
    if not model: return False
    
    # Embed Candidate
    # text is typically "title + summary"
    candidate_vec = model.encode([text], convert_to_numpy=True)[0]
    
    from sklearn.metrics.pairwise import cosine_similarity
    scores = cosine_similarity([candidate_vec], _rejected_embeddings)[0]
    
    max_score = np.max(scores)
    
    if max_score > threshold:
        # Debug Log
        idx = np.argmax(scores)
        matched_text = _rejected_texts[idx][:50] + "..."
        print(f"Content Filter Triggered: Score {max_score:.2f} (Match: {matched_text})")
        return True
        
    return False
