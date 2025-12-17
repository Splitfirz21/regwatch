import sys
import os
import json
from datetime import datetime

# Add the backend directory to sys.path
sys.path.append(os.path.abspath("backend"))

try:
    import scraper
    # Mock the dependencies if needed or just run it
    
    print("Testing 'autonomous vehicles' search...")
    result = scraper.search_news("autonomous vehicles")
    
    # Check type
    print(f"Result Type: {type(result)}")
    
    if isinstance(result, dict):
        print(f"Keys: {result.keys()}")
        if "items" in result:
            print(f"Items Type: {type(result['items'])}")
            print(f"Items Length: {len(result['items'])}")
            if len(result['items']) > 0:
                print(f"First Item: {result['items'][0]}")
    else:
        print("Result is not a dict!")
        print(result)

except Exception as e:
    print(f"Error during reproduction: {e}")
