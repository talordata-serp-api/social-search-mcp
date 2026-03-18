from googlesearch import search
import time

def test():
    q = "rent in new york site:reddit.com"
    print(f"Testing Google Search: '{q}'")
    
    try:
        results = search(q, num_results=3, advanced=True)
        for r in results:
            print(f"Title: {r.title}")
            print(f"URL: {r.url}")
            print(f"Description: {r.description}\\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
