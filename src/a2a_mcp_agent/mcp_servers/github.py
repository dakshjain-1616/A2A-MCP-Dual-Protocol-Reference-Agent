"""GitHub MCP Server - Provides GitHub API operations."""

import asyncio
import json
import os
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
server = Server("github-server")
GITHUB_API_BASE = "https://api.github.com"


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available GitHub tools."""
    return [
        Tool(
            name="search_repositories",
            description="Search for GitHub repositories",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'language:python stars:>1000')",
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 5, max: 10)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_repository",
            description="Get details about a specific repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner (user or org)",
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name",
                    },
                },
                "required": ["owner", "repo"],
            },
        ),
        Tool(
            name="list_issues",
            description="List issues in a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner",
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name",
                    },
                    "state": {
                        "type": "string",
                        "description": "Issue state: open, closed, all",
                        "default": "open",
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["owner", "repo"],
            },
        ),
        Tool(
            name="get_readme",
            description="Get README content of a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner",
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name",
                    },
                },
                "required": ["owner", "repo"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    settings = get_settings()
    
    if name == "search_repositories":
        return await _handle_search_repositories(arguments, settings)
    elif name == "get_repository":
        return await _handle_get_repository(arguments, settings)
    elif name == "list_issues":
        return await _handle_list_issues(arguments, settings)
    elif name == "get_readme":
        return await _handle_get_readme(arguments, settings)
    else:
        raise ValueError(f"Unknown tool: {name}")


def _get_headers(settings: Any) -> dict[str, str]:
    """Get GitHub API headers."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "A2A-MCP-Agent/0.1.0",
    }
    if settings.github_token:
        headers["Authorization"] = f"token {settings.github_token}"
    return headers


async def _handle_search_repositories(
    arguments: dict[str, Any], settings: Any
) -> list[TextContent]:
    """Handle search repositories tool call."""
    query = arguments.get("query", "")
    per_page = min(arguments.get("per_page", 5), 10)
    
    logger.info(f"GitHub search: {query}")
    
    if settings.is_mock_mode:
        logger.info("Using mock GitHub search results")
        mock_results = {
            "total_count": 3,
            "items": [
                {
                    "name": f"mock-repo-{i}",
                    "full_name": f"user/mock-repo-{i}",
                    "description": f"Mock repository {i} for query: {query}",
                    "stars": 100 + i * 50,
                    "language": "Python",
                    "url": f"https://github.com/user/mock-repo-{i}",
                }
                for i in range(per_page)
            ],
        }
        return [TextContent(type="text", text=json.dumps(mock_results, indent=2))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/search/repositories",
                headers=_get_headers(settings),
                params={"q": query, "per_page": per_page},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
            results = {
                "total_count": data.get("total_count", 0),
                "items": [
                    {
                        "name": item.get("name"),
                        "full_name": item.get("full_name"),
                        "description": item.get("description"),
                        "stars": item.get("stargazers_count"),
                        "language": item.get("language"),
                        "url": item.get("html_url"),
                    }
                    for item in data.get("items", [])
                ],
            }
            return [TextContent(type="text", text=json.dumps(results, indent=2))]
    except Exception as e:
        logger.error(f"GitHub search error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_get_repository(
    arguments: dict[str, Any], settings: Any
) -> list[TextContent]:
    """Handle get repository tool call."""
    owner = arguments.get("owner", "")
    repo = arguments.get("repo", "")
    
    logger.info(f"Getting repository: {owner}/{repo}")
    
    if settings.is_mock_mode:
        mock_repo = {
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "description": f"Mock repository {owner}/{repo}",
            "stars": 500,
            "forks": 50,
            "open_issues": 10,
            "language": "Python",
            "url": f"https://github.com/{owner}/{repo}",
        }
        return [TextContent(type="text", text=json.dumps(mock_repo, indent=2))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
                headers=_get_headers(settings),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
            result = {
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "open_issues": data.get("open_issues_count"),
                "language": data.get("language"),
                "url": data.get("html_url"),
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.error(f"GitHub get repo error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_list_issues(
    arguments: dict[str, Any], settings: Any
) -> list[TextContent]:
    """Handle list issues tool call."""
    owner = arguments.get("owner", "")
    repo = arguments.get("repo", "")
    state = arguments.get("state", "open")
    per_page = min(arguments.get("per_page", 5), 10)
    
    logger.info(f"Listing issues: {owner}/{repo}")
    
    if settings.is_mock_mode:
        mock_issues = [
            {
                "number": i + 1,
                "title": f"Mock Issue {i+1}",
                "state": state,
                "body": f"This is a mock issue for {owner}/{repo}",
                "url": f"https://github.com/{owner}/{repo}/issues/{i+1}",
            }
            for i in range(per_page)
        ]
        return [TextContent(type="text", text=json.dumps(mock_issues, indent=2))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                headers=_get_headers(settings),
                params={"state": state, "per_page": per_page},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
            issues = [
                {
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "body": item.get("body", "")[:500] if item.get("body") else "",
                    "url": item.get("html_url"),
                }
                for item in data
            ]
            return [TextContent(type="text", text=json.dumps(issues, indent=2))]
    except Exception as e:
        logger.error(f"GitHub list issues error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_get_readme(
    arguments: dict[str, Any], settings: Any
) -> list[TextContent]:
    """Handle get README tool call."""
    owner = arguments.get("owner", "")
    repo = arguments.get("repo", "")
    
    logger.info(f"Getting README: {owner}/{repo}")
    
    if settings.is_mock_mode:
        mock_readme = f"# {repo}\n\nThis is a mock README for {owner}/{repo}.\n\n## Features\n\n- Feature 1\n- Feature 2\n- Feature 3\n"
        return [TextContent(type="text", text=mock_readme)]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme",
                headers=_get_headers(settings),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
            import base64
            content = base64.b64decode(data.get("content", "")).decode("utf-8")
            return [TextContent(type="text", text=content[:5000])]
    except Exception as e:
        logger.error(f"GitHub get README error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


class GitHubServer:
    """GitHub MCP Server wrapper."""

    def __init__(self) -> None:
        """Initialize the server."""
        self.name = "github-server"

    async def list_tools(self) -> list[Tool]:
        """Proxy to module-level list_tools."""
        return await list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Proxy to module-level call_tool."""
        return await call_tool(name, arguments)

    async def run(self) -> None:
        """Run the server."""
        async with stdio_server(server) as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Main entry point."""
    server_instance = GitHubServer()
    asyncio.run(server_instance.run())


if __name__ == "__main__":
    main()
