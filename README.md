# Social Search MCP Server

<!-- mcp-name: io.github.shubhamekapure/social-search-mcp -->
A Model Context Protocol (MCP) server that empowers LLMs to search across specific social media platforms using the industry's best search engines.

## Overview
This server provides a `search_social` tool that accepts a query and an optional list of platforms (facebook, reddit, linkedin, etc.). It filters results exclusively to those domains and returns them directly to the LLM context.

## Search Providers

You can configure the backend by setting the `SEARCH_PROVIDER` environment variable. By default, it uses **SearXNG** since it is free and open-source.

### 1. SearXNG (Default)
SearXNG is a free, open-source internet metasearch engine.
- `SEARCH_PROVIDER=searxng`
- `SEARXNG_URL=http://localhost:8080` (Defaults to localhost, specify a remote public instance if you don't host your own, but note that public instances often limit automated JSON requests).

### 2. Serper.dev
A powerful Google Search wrapper API. Highly recommended for accurate results.
- `SEARCH_PROVIDER=serper`
- `SERPER_API_KEY=your_key` (Get one from [Serper.dev](https://serper.dev/))

### 3. Google Custom Search
The official Google Custom Search API.
- `SEARCH_PROVIDER=google`
- `GOOGLE_API_KEY=your_key`
- `GOOGLE_CX=your_cx_engine_id`

### 4. TalorData

A fast and cost-effective Google Search API tailored for AI Agents.

- `SEARCH_PROVIDER=talordata`
- `TALORDATA_API_KEY=your_key` (Get one from [talordata.com](https://talordata.com/?campaignid=9Xaq0RfSFf7RS4Xe&utm_source=ssm&utm_term=ssm))

## Setup
Ensure you have Python 3.10+ installed.

```bash
# Clone or place in a directory, then:
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "social-search-mcp": {
      "command": "/ABSOLUTE/PATH/TO/venv/bin/social-search-mcp",
      "args": [],
      "env": {
        "SEARCH_PROVIDER": "searxng",
        "SEARXNG_URL": "http://localhost:8080"
      }
    }
  }
}
```
Replace `/ABSOLUTE/PATH/TO/` with the actual path to this folder. Restart Claude Desktop after updating the config.
