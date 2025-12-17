
import requests
import io
import pandas as pd

def test_export():
    try:
        url = "http://localhost:3005/export" # Wait, export is separate endpoint?
        # Actually export is usually on API (8005), but frontend might proxy it?
        # App.jsx: window.open(`${API_Base}/export`, '_blank')
        # API_Base is 8005. So we hit port 8005.
        
        url = "http://localhost:8005/export"
        
        print(f"Fetching export from {url}...")
        res = requests.get(url, stream=True)
        
        print(f"Status Code: {res.status_code}")
        print(f"Headers: {res.headers}")
        
        if res.status_code == 200:
            content = res.content
            print(f"Content Length: {len(content)} bytes")
            print(f"First 50 bytes: {content[:50]}")
            
            # Try to read with pandas
            try:
                df = pd.read_excel(io.BytesIO(content))
                print("SUCCESS: Valid Excel file.")
                print(df.head())
            except Exception as e:
                print(f"FAIL: Invalid Excel file. Error: {e}")
                print(f"Content Preview (Text): {content[:200]}")
        else:
            print(f"FAIL: Non-200 status. {res.text}")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_export()
