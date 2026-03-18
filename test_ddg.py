from duckduckgo_search import DDGS

def test():
    ddgs = DDGS()
    
    q = "rent in new york facebook"
    print(f"Test 6: '{q}'")
    res6 = list(ddgs.text(q, max_results=3))
    for r in res6:
        print(r)

    q = "rent in new york reddit"
    print(f"\\nTest 7: '{q}'")
    res7 = list(ddgs.text(q, max_results=3))
    for r in res7:
        print(r)

if __name__ == "__main__":
    test()
