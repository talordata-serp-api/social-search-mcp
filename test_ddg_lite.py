import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_ddg_lite(query, max_results=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching DDG: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    for a in soup.find_all('a', class_='result__snippet', limit=max_results):
        href = a.get('href')
        if href and href.startswith('//duckduckgo.com/l/?uddg='):
            href = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
            
        # Get title
        title_tag = a.find_previous('a', class_='result__url')
        if not title_tag:
            title_tag = a.find_previous('h2', class_='result__title')

        title = title_tag.text.strip() if title_tag else "No title"
        snippet = a.text.strip()
        
        results.append({
            "title": title,
            "url": href,
            "snippet": snippet
        })
        
    return results

if __name__ == "__main__":
    q = "rent in new york site:reddit.com"
    print(f"Testing DDG Lite: '{q}'")
    res = search_ddg_lite(q, max_results=3)
    for r in res:
        print(r)
    print(f"Total: {len(res)}")
