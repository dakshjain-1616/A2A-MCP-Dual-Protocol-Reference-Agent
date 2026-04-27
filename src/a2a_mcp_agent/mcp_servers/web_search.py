"""Web Search MCP Server - Provides web search capabilities."""

import asyncio
import json
import sys
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from a2a_mcp_agent.config import get_settings
from a2a_mcp_agent.utils.logging import get_logger

logger = get_logger(__name__)

# Server instance
server = Server("web-search-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available web search tools."""
    return [
        Tool(
            name="web_search",
            description="Search the web for information using a query string",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to execute",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_page_content",
            description="Fetch and extract content from a specific URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch content from",
                    },
                },
                "required": ["url"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    settings = get_settings()
    
    if name == "web_search":
        return await _handle_web_search(arguments, settings)
    elif name == "get_page_content":
        return await _handle_get_page_content(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _handle_web_search(
    arguments: dict[str, Any], settings: Any
) -> list[TextContent]:
    """Handle web search tool call."""
    query = arguments.get("query", "")
    num_results = arguments.get("num_results", 5)
    
    logger.info(f"Web search: {query}")
    
    # Check for mock mode or missing API key
    if settings.is_mock_mode or not settings.serper_api_key:
        logger.info("Using mock web search results")
        mock_results = [
            {
                "title": f"Mock Result {i+1} for '{query}'",
                "link": f"https://example.com/result{i+1}",
                "snippet": f"This is a mock search result snippet for query: {query}",
            }
            for i in range(min(num_results, 3))
        ]
        return [TextContent(type="text", text=json.dumps(mock_results, indent=2))]
    
    # Real search using Serper API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": settings.serper_api_key},
                json={"q": query, "num": num_results},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("organic", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            
            return [TextContent(type="text", text=json.dumps(results, indent=2))]
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_get_page_content(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle get page content tool call."""
    url = arguments.get("url", "")
    
    logger.info(f"Fetching page: {url}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            
            # Simple text extraction (in production, use BeautifulSoup)
            content = response.text[:5000]  # Limit content length
            return [TextContent(type="text", text=content)]
    except Exception as e:
        logger.error(f"Page fetch error: {e}")
        return [TextContent(type="text", text=f"Error fetching {url}: {str(e)}")]


class WebSearchServer:
    """Web Search MCP Server wrapper."""

    def __init__(self) -> None:
        """Initialize the server."""
        self.name = "web-search-server"

    async def list_tools(self) -> list[Tool]:
        """Proxy to the module-level list_tools handler."""
        return await list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Proxy to the module-level call_tool handler."""
        return await call_tool(name, arguments)

    async def run(self) -> None:
        """Run the server."""
        async with stdio_server(server) as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Main entry point."""
    server_instance = WebSearchServer()
    asyncio.run(server_instance.run())


if __name__ == "__main__":
    main()
