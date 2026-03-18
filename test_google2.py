from googlesearch import search

def test():
    q = "rent in new york site:reddit.com"
    print(f"Testing Google Search: '{q}'")
    
    try:
        # advanced=False is the default and yields URLs
        results = list(search(q, num_results=3, lang="en"))
        print(f"Got {len(results)} results:")
        for r in results:
            print(r)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
