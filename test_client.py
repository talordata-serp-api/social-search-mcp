import asyncio
from social_search_mcp.server import handle_call_tool

async def run_test():
    print("Testing social search tool with Google...")
    
    args = {
        "query": "rent 2bhk in sector 43 gurgaon",
        "platforms": ["facebook", "reddit"],
        "max_results": 2
    }
    
    try:
        results = await handle_call_tool("search_social", args)
        print("Results received successfully:")
        for r in results:
            print("---")
            print(r.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
