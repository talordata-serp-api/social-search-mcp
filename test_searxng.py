import requests
import json

def test_searxng():
    # A few known public instances
    instances = [
        "https://searx.be",
        "https://searx.tiekoetter.com",
        "https://search.mdosch.de",
        "https://paulgo.io"
    ]
    
    for instance in instances:
        print(f"Testing {instance}...")
        url = f"{instance}/search"
        params = {
            "q": "rent 2bhk in sector 43 gurgaon site:reddit.com",
            "format": "json",
            "time_range": "month"
        }
        try:
            r = requests.get(url, params=params, timeout=5)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                print(f"SUCCESS! Got {len(results)} results.")
                if results:
                    print(f"Sample: {results[0].get('title')}")
                return instance
            else:
                print(f"Failed with status: {r.status_code}")
        except Exception as e:
            print(f"Error: {e}")
            
    return None

if __name__ == "__main__":
    best = test_searxng()
    print(f"Best instance: {best}")
