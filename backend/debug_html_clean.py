from bs4 import BeautifulSoup
import html

def test_clean():
    # Content reconstructed from screenshot
    # It shows: <a href="https://news.google.com/rss/articles/..." target="_blank">MND trims...</a>
    # If this appears as text, it means the input string was likely:
    # "&lt;a href=&quot;...&quot;&gt;..."
    
    raw_input_1 = '<a href="https://example.com">Link Text</a>' # Normal HTML
    raw_input_2 = '&lt;a href="https://example.com"&gt;Link Text&lt;/a&gt;' # Escaped HTML
    
    print(f"--- Input 1: {raw_input_1} ---")
    soup1 = BeautifulSoup(raw_input_1, 'lxml')
    print(f"BS4 Direct: {soup1.get_text()!r}")
    
    print(f"\n--- Input 2: {raw_input_2} ---")
    soup2 = BeautifulSoup(raw_input_2, 'lxml')
    print(f"BS4 Direct: {soup2.get_text()!r}") 
    # ^ Expected: '&lt;a href="...&gt;Link Text&lt;/a&gt;' (BS4 treats it as text)
    
    unescaped = html.unescape(raw_input_2)
    print(f"Unescaped: {unescaped!r}")
    soup3 = BeautifulSoup(unescaped, 'lxml')
    print(f"BS4 after Unescape: {soup3.get_text()!r}")
    # ^ Expected: 'Link Text'
    
    # What if it's DOUBLE escaped?
    raw_input_3 = '&amp;lt;a href=&quot;...&quot;&amp;gt;'
    print(f"\n--- Input 3 (Double): {raw_input_3} ---")
    unescaped3 = html.unescape(html.unescape(raw_input_3)) # Simulate dual
    print(f"Unescaped x2: {unescaped3!r}")

test_clean()
