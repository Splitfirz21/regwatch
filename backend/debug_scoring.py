from scraper import calculate_relevance_score

test_cases = [
    # Should Pass (Score > 15)
    "New bill passed to enhance food safety standards",
    "MOM announces updated guidelines for workplace safety",
    "Singapore to implement new carbon tax framework in 2026",
    
    # Borderline (Should Pass or be close)
    "URA releases circular on show-flat requirements",
    "BCA launches new grant for green buildings",
    
    # Should Fail (Score < 15)
    "DBS net profit rises 20% in Q3",
    "Singapore Airlines share price drops after earnings",
    "Standard Chartered Marathon road closures announced",
    "US sanctions Iranian oil trade entities",
    "Top 10 richest people in Singapore",
    "New restaurant opens in Jewel Changi Airport"
]

print(f"{'Headline':<60} | {'Score':<5} | {'Pass?':<5}")
print("-" * 75)

for headline in test_cases:
    score = calculate_relevance_score(headline)
    passed = score >= 15
    print(f"{headline[:58]:<60} | {score:<5} | {str(passed):<5}")
