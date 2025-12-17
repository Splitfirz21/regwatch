
import scorer
import re

def debug_impact_triggers():
    examples = [
        ("Singapore, Malaysia to ramp up cross-border taxi quota", "drivers can now ply..."),
        ("Singapore to invest S$37 billion in research", "RIE2025 plan..."),
        ("Cross-border taxis more attractive with flexible daily quota", "New rules..."),
        ("Bill passed to regulate AI", "Parliament..."), # Control case
    ]
    
    print(f"{'Title':<50} | Impact | Triggers")
    print("-" * 80)
    
    for title, summary in examples:
        text = (title + " " + summary).lower()
        impact = scorer.analyze_impact(title, summary)
        
        # Find triggers manually to see what matched
        triggers = []
        if impact == "High":
            for k in scorer.IMPACT_KEYWORDS["High"]:
                if k in text:
                    triggers.append(k)
        
        print(f"{title[:48]:<50} | {impact:<6} | {triggers}")

if __name__ == "__main__":
    debug_impact_triggers()
