import asyncio
import os
import requests
import json
from typing import Optional, List
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

PLATFORMS = {
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "twitter": "twitter.com",
    "reddit": "reddit.com",
    "linkedin": "linkedin.com",
    "snapchat": "snapchat.com",
    "tiktok": "tiktok.com",
    "pinterest": "pinterest.com",
    "x": "x.com"
}

server = Server("social-search-mcp")

def search_searxng(query: str, max_results: int = 10, time_filter: str = None):
    searxng_url = os.environ.get("SEARXNG_URL", "http://localhost:8080")
    
    url = f"{searxng_url.rstrip('/')}/search"
    params = {
        "q": query,
        "format": "json"
    }
    
    if time_filter:
        # SearXNG uses day, week, month, year
        if time_filter in ["day", "week", "month", "year"]:
            params["time_range"] = time_filter
            
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return f"SearXNG Error ({response.status_code}): {response.text}"
        data = response.json()
    except Exception as e:
        return f"Error connecting to SearXNG at {searxng_url}: {e}\\nMake sure your SearXNG instance is running and accessible."

    results = []
    for item in data.get("results", [])[:max_results]:
        results.append({
            "title": item.get("title", "No Title"),
            "url": item.get("url", ""),
            "snippet": item.get("content", "")
        })
    return results

def search_serper(query: str, max_results: int = 10, time_filter: str = None, gl: str = None, hl: str = None):
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return "ERROR: Missing `SERPER_API_KEY` environment variable."
        
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "num": min(max_results, 100)
    }
    
    if gl:
        payload["gl"] = gl
    if hl:
        payload["hl"] = hl
    
    if time_filter:
        time_mapping = {"day": "qdr:d", "week": "qdr:w", "month": "qdr:m", "year": "qdr:y"}
        if time_filter in time_mapping:
            payload["tbs"] = time_mapping[time_filter]
            
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code != 200:
            return f"Serper API Error: {response.text}"
        data = response.json()
    except Exception as e:
        return f"Error connecting to Serper: {e}"

    results = []
    for item in data.get("organic", [])[:max_results]:
        results.append({
            "title": item.get("title", "No Title"),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", "")
        })
    return results

def search_google(query: str, max_results: int = 10, time_filter: str = None):
    api_key = os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CX")
    if not api_key or not cx:
        return "ERROR: Missing `GOOGLE_API_KEY` and `GOOGLE_CX` environment variables."

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(10, max_results)
    }
    
    if time_filter:
        time_mapping = {"day": "d1", "week": "w1", "month": "m1", "year": "y1"}
        if time_filter in time_mapping:
            params["dateRestrict"] = time_mapping[time_filter]
            
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            err_msg = response.json().get('error', {}).get('message', 'Unknown Error')
            return f"Google API Error ({response.status_code}): {err_msg}"
        data = response.json()
    except Exception as e:
        return f"Error connecting to Google API: {e}"

    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("title", "No Title"),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", "")
        })
    return results

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_social",
            description=(
                "Search social media platforms (Facebook, Reddit, LinkedIn, Instagram, Twitter/X, TikTok, Pinterest, Snapchat) "
                "for real-world content like rental listings, second-hand items, events, job posts, community discussions, and more. "
                "Use this instead of a regular web search when the user is looking for content posted by real people on social platforms. "
                "\n\nCommon use cases:\n"
                "- Rental listings (2BHK, apartments, PGs, rooms): search facebook + reddit\n"
                "- Second-hand items or marketplace deals: search facebook\n"
                "- Professional networking or job posts: search linkedin\n"
                "- Local events or meetups: search facebook + reddit + linkedin\n"
                "- Tech discussions, recommendations, or opinions: search reddit + twitter\n"
                "- Trending topics or news reactions: search twitter + reddit\n"
                "\nALWAYS infer the right platforms from context. If the user mentions India, set gl='in'. "
                "If the user asks for recent results, use time_filter='week' or 'month'. "
                "Do NOT ask the user to specify platforms or gl — infer them yourself from the query context."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The exact search query. Be specific — include location, item type, and key details. "
                            "Example: 'rent 2BHK fully furnished apartment sector 43 Gurgaon' or 'used iPhone 15 pro max for sale Mumbai'."
                        )
                    },
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Social platforms to restrict the search to. Infer from context:\n"
                            "- 'facebook': best for rentals, second-hand goods, local groups, events\n"
                            "- 'reddit': best for reviews, recommendations, community discussions\n"
                            "- 'linkedin': best for jobs, professional events, company updates\n"
                            "- 'twitter' or 'x': best for trending topics, real-time news, opinions\n"
                            "- 'instagram': best for brand content, lifestyle, visual discovery\n"
                            "- 'tiktok': best for viral trends, short video content\n"
                            "- 'pinterest': best for ideas, design inspiration, DIY\n"
                            "If unsure, default to ['facebook', 'reddit']. Leave empty to search all platforms."
                        )
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return. Default is 10. Max is 30. Use more for broader discovery, fewer for focused answers."
                    },
                    "time_filter": {
                        "type": "string",
                        "description": (
                            "Filter results by recency. Use this when the user wants recent or up-to-date info:\n"
                            "- 'day': past 24 hours — use for breaking news or very fresh listings\n"
                            "- 'week': past 7 days — good default for rentals, events, job posts\n"
                            "- 'month': past 30 days — broader discovery\n"
                            "- 'year': past year — for long-term research\n"
                            "Omit entirely for relevance-based results (all time)."
                        )
                    },
                    "gl": {
                        "type": "string",
                        "description": (
                            "Geolocation country code to bias results toward a specific country. "
                            "ALWAYS set this based on context:\n"
                            "- 'in' → India (Gurgaon, Mumbai, Bangalore, Delhi, etc.)\n"
                            "- 'us' → United States\n"
                            "- 'gb' → United Kingdom\n"
                            "- 'au' → Australia\n"
                            "- 'ca' → Canada\n"
                            "- 'sg' → Singapore\n"
                            "- 'ae' → UAE / Dubai\n"
                            "Default to 'us' if no location is evident from the query."
                        )
                    },
                    "hl": {
                        "type": "string",
                        "description": (
                            "Language code for results. Use 'hi' for Hindi, 'en' for English. "
                            "Only set if the user explicitly asks for a non-English language."
                        )
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name != "search_social":
        raise ValueError(f"Unknown tool: {name}")

    if not arguments or "query" not in arguments:
        raise ValueError("Missing required 'query' argument")

    query = arguments.get("query")
    requested_platforms = arguments.get("platforms", [])
    max_results = min(arguments.get("max_results", 10), 30)
    time_filter = arguments.get("time_filter")
    gl = arguments.get("gl")
    hl = arguments.get("hl")

    domains = []
    if requested_platforms:
        for p in requested_platforms:
            p_lower = p.lower()
            if p_lower in PLATFORMS:
                domains.append(PLATFORMS[p_lower])
            elif "." in p_lower:
                domains.append(p_lower)
    else:
        domains = list(PLATFORMS.values())

    site_query = " OR ".join([f"site:{d}" for d in domains])
    final_query = f"{query} ({site_query})".strip()

    provider = os.environ.get("SEARCH_PROVIDER", "searxng").lower()
    
    if provider == "searxng":
        results = search_searxng(final_query, max_results=max_results, time_filter=time_filter)
    elif provider == "serper":
        results = search_serper(final_query, max_results=max_results, time_filter=time_filter, gl=gl, hl=hl)
    elif provider == "google":
        results = search_google(final_query, max_results=max_results, time_filter=time_filter)
    else:
        return [types.TextContent(type="text", text=f"ERROR: Unknown SEARCH_PROVIDER '{provider}'. Use 'searxng', 'serper', or 'google'.")]

    if isinstance(results, str):  # Error message returned
        return [types.TextContent(type="text", text=results)]
        
    if not results:
        return [types.TextContent(type="text", text=f"No results found from provider '{provider}'.")]

    formatted_results = "\\n\\n".join(
        [f"Title: {r.get('title')}\\nURL: {r.get('url')}\\nSnippet: {r.get('snippet')}" for r in results]
    )

    return [types.TextContent(type="text", text=formatted_results)]

async def run_server():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="social-search-mcp",
                server_version="0.1.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
