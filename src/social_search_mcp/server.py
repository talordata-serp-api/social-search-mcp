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

def search_talordata(query: str, max_results: int = 10, time_filter: str = None) -> list:
    """使用 TalorData SERP API 进行搜索并返回统一格式的列表"""
    import requests
    
    api_key = os.environ.get("TALORDATA_API_KEY")
    if not api_key:
        return "ERROR: Missing `TALORDATA_API_KEY` environment variable."
        
    # TalorData 标准 Google 搜索端点
    url = "https://talordata.com" 
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "engine": "google"
    }
    
    # 兼容原项目的过滤参数
    if time_filter:
        payload["time_filter"] = time_filter

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"TalorData Error ({response.status_code}): {response.text}"
            
        data = response.json()
        
        # 提取 TalorData 的自然搜索结果列表（通常是 organic_results）
        raw_results = data.get("organic_results", [])[:max_results]
        
        # 将其转化为原项目标准格式并返回
        results = []
        for item in raw_results:
            results.append({
                "title": item.get("title", "No Title"),
                "url": item.get("link", item.get("url", "")),
                "snippet": item.get("snippet", item.get("description", ""))
            })
        return results
        
    except Exception as e:
        return f"Error connecting to TalorData: {str(e)}"

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
            description="Perform a web search focused ONLY on specific social media platforms.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g. '2bhk rent sector 43', 'used mountain bike', 'AI networking events')"
                    },
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Social platforms to target. Highly recommended: 'facebook' (rentals/marketplace), 'reddit' (discussions/advice), 'linkedin' (jobs/networking), 'instagram', 'twitter', 'tiktok', 'snapchat', 'pinterest'."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results (1-10). Note: High counts may hit API limits on some backends."
                    },
                    "time_filter": {
                        "type": "string",
                        "description": "Find recent content. Options: 'day' (last 24h), 'week', 'month', 'year'. Default is all time/relevance."
                    },
                    "gl": {
                        "type": "string",
                        "description": "Two-letter country code for regional targeting (e.g. 'in' for India, 'us' for USA, 'gb' for UK). Crucial for localized queries like neighborhood rentals."
                    },
                    "hl": {
                        "type": "string",
                        "description": "Language code for the search results (e.g. 'en', 'hi', 'es')."
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
elif provider == "talordata":
    results = search_talordata(final_query, max_results=max_results, time_filter=time_filter)
else:
    return [types.TextContent(type="text", text=f"ERROR: Unknown SEARCH_PROVIDER '{provider}'. Use 'searxng', 'serper', 'google', or 'talordata'.")]

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
