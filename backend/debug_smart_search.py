def extract_keywords(user_query):
    print(f"Original: '{user_query}'")
    
    # OLD LOGIC (Simulation)
    old_fallback = []
    ignored_generic_old = ["DPM", "PM", "Minister", "Speech", "Regulations", "Act", "Bill", "Singapore", "New", "Update", "The", "A", "An", "On", "At", "For", "Of", "In", "And", "To", "With", "By"]
    for word in user_query.split():
        clean_word = word.strip(".,()[]{}'\"")
        if clean_word.isdigit():
            old_fallback.append(clean_word)
        elif clean_word and clean_word[0].isupper() and clean_word not in ignored_generic_old and len(clean_word) > 1:
            old_fallback.append(clean_word)
    print(f"Old Logic Result: {old_fallback}")

    # NEW LOGIC (Proposed)
    stopwords = {
        "at", "on", "in", "to", "for", "of", "the", "a", "an", "and", "or", "is", "are", "with", "by",
        "speech", "statement", "press", "release", "news", "update", "report",
        "minister", "ministry", "dpm", "pm", "secretary", "government",
        "regulations", "regulation", "act", "bill", "law", "policy", "guidelines", "framework",
        "singapore", "sg", "new", "latest"
    }
    
    tokens = user_query.lower().split()
    clean_tokens = []
    for t in tokens:
        # Strip punctuation
        t_clean = t.strip(".,()[]{}'\"")
        if t_clean and t_clean not in stopwords:
            clean_tokens.append(t_clean)
            
    print(f"New Logic Result: {clean_tokens}")
    return clean_tokens

extract_keywords("dpm speech at pep awards 2025 on regulations")
extract_keywords("DPM Speech at PEP Awards 2025 on Regulations")
