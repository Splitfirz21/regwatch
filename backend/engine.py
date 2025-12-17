from typing import List, Dict
from models import NewsItem, Feedback
from collections import defaultdict

class RelevanceEngine:
    def __init__(self):
        self.sector_scores = defaultdict(float)
        self.keyword_penalties = defaultdict(float)

    def extract_keywords(self, text: str) -> List[str]:
        # Simple stopword removal and splitting
        stopwords = set(["the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "to", "for", "of", "in", "on", "at", "by", "from", "with"])
        words = text.lower().split()
        return [w for w in words if w.isalpha() and w not in stopwords and len(w) > 3]

    def train(self, feedbacks: List[Feedback], news_map: Dict[int, NewsItem]):
        # Reset scores
        self.sector_scores = defaultdict(float)
        self.keyword_penalties = defaultdict(float)
        
        for fb in feedbacks:
            if fb.news_item_id in news_map:
                item = news_map[fb.news_item_id]
                score = 1.0 if fb.liked else -0.5
                self.sector_scores[item.sector] += score
                
                if not fb.liked:
                    # HEAVY penalty for removed/disliked items keywords
                    # This helps "avoid similar news"
                    kws = self.extract_keywords(item.title)
                    for kw in kws:
                        self.keyword_penalties[kw] += 0.5 # Accumulate penalty

    def rank(self, items: List[NewsItem]) -> List[NewsItem]:
        
        def get_score(item):
            base_score = self.sector_scores.get(item.sector, 0.0)
            
            # Checks constraints/penalties
            penalty = 0.0
            kws = self.extract_keywords(item.title)
            for kw in kws:
                penalty += self.keyword_penalties.get(kw, 0.0)
            
            return base_score - penalty

        # Sort descending by score
        return sorted(items, key=get_score, reverse=True)

engine = RelevanceEngine()
