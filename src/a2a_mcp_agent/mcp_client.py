"""MCP Client for orchestrating tool calls across multiple MCP servers."""

import asyncio
import json
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from a2a_mcp_agent.config import get_settings
from a2a_mcp_agent.utils.logging import get_logger

logger = get_logger(__name__)


class MCPClient:
    """Client for managing multiple MCP server connections."""
    
    def __init__(self) -> None:
        """Initialize the MCP client."""
        self.sessions: dict[str, ClientSession] = {}
        self.tools: dict[str, list[dict[str, Any]]] = {}
        self.settings = get_settings()
    
    async def connect_server(
        self, name: str, command: str, args: list[str] | None = None
    ) -> None:
        """Connect to an MCP server.
        
        Args:
            name: Server identifier
            command: Command to run the server
            args: Arguments for the command
        """
        args = args or []
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None,
        )
        
        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                session = ClientSession(read_stream, write_stream)
                await session.initialize()
                
                # List available tools
                tools_response = await session.list_tools()
                tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    for tool in tools_response.tools
                ]
                
                self.sessions[name] = session
                self.tools[name] = tools
                logger.info(f"Connected to MCP server '{name}' with {len(tools)} tools")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{name}': {e}")
            raise
    
    async def connect_all_servers(self) -> None:
        """Connect to all configured MCP servers."""
        # Connect to built-in MCP servers
        servers = [
            ("web_search", "python", ["-m", "a2a_mcp_agent.mcp_servers.web_search"]),
            ("file_system", "python", ["-m", "a2a_mcp_agent.mcp_servers.file_system"]),
            ("github", "python", ["-m", "a2a_mcp_agent.mcp_servers.github"]),
        ]
        
        for name, command, args in servers:
            try:
                await self.connect_server(name, command, args)
            except Exception as e:
                logger.warning(f"Could not connect to {name} server: {e}")
    
    def get_all_tools(self) -> list[dict[str, Any]]:
        """Get all tools from all connected servers.
        
        Returns:
            List of tool definitions with server prefix
        """
        all_tools = []
        for server_name, tools in self.tools.items():
            for tool in tools:
                # Prefix tool name with server name to avoid conflicts
                tool_copy = tool.copy()
                tool_copy["original_name"] = tool["name"]
                tool_copy["name"] = f"{server_name}__{tool['name']}"
                tool_copy["server"] = server_name
                all_tools.append(tool_copy)
        return all_tools
    
    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """Get tools formatted for LLM function calling.
        
        Returns:
            List of tool definitions in OpenAI format
        """
        all_tools = self.get_all_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"],
                },
            }
            for tool in all_tools
        ]
    
    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> str:
        """Call a tool on a specific server.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result as string
        """
        if server_name not in self.sessions:
            raise ValueError(f"Server '{server_name}' not connected")
        
        session = self.sessions[server_name]
        
        try:
            result = await session.call_tool(tool_name, arguments)
            # Extract text content from result
            texts = []
            for content in result.content:
                if content.type == "text":
                    texts.append(content.text)
            return "\n".join(texts)
        except Exception as e:
            logger.error(f"Tool call error on {server_name}.{tool_name}: {e}")
            return f"Error: {str(e)}"
    
    async def call_tool_by_full_name(
        self, full_tool_name: str, arguments: dict[str, Any]
    ) -> str:
        """Call a tool using its full name (server__tool).
        
        Args:
            full_tool_name: Full tool name with server prefix
            arguments: Tool arguments
            
        Returns:
            Tool result as string
        """
        if "__" not in full_tool_name:
            raise ValueError(f"Invalid tool name format: {full_tool_name}")
        
        server_name, tool_name = full_tool_name.split("__", 1)
        return await self.call_tool(server_name, tool_name, arguments)
    
    async def close(self) -> None:
        """Close all MCP connections."""
        for name, session in self.sessions.items():
            try:
                await session.close()
                logger.info(f"Closed MCP connection to '{name}'")
            except Exception as e:
                logger.warning(f"Error closing session '{name}': {e}")
        self.sessions.clear()
        self.tools.clear()


class MockMCPClient:
    """Mock MCP client for testing without real servers."""
    
    def __init__(self) -> None:
        """Initialize mock client."""
        self.tools = {
            "web_search": [
                {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "num_results": {"type": "integer", "default": 5},
                        },
                        "required": ["query"],
                    },
                },
            ],
            "file_system": [
                {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
                {
                    "name": "write_file",
                    "description": "Write content to a file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["path", "content"],
                    },
                },
            ],
            "github": [
                {
                    "name": "search_repositories",
                    "description": "Search for GitHub repositories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "per_page": {"type": "integer", "default": 5},
                        },
                        "required": ["query"],
                    },
                },
            ],
        }
    
    async def connect_all_servers(self) -> None:
        """No-op for mock client."""
        logger.info("Mock MCP client initialized")
    
    def get_all_tools(self) -> list[dict[str, Any]]:
        """Get mock tools."""
        all_tools = []
        for server_name, tools in self.tools.items():
            for tool in tools:
                tool_copy = tool.copy()
                tool_copy["original_name"] = tool["name"]
                tool_copy["name"] = f"{server_name}__{tool['name']}"
                tool_copy["server"] = server_name
                all_tools.append(tool_copy)
        return all_tools
    
    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """Get tools formatted for LLM."""
        all_tools = self.get_all_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"],
                },
            }
            for tool in all_tools
        ]
    
    async def call_tool_by_full_name(
        self, full_tool_name: str, arguments: dict[str, Any]
    ) -> str:
        """Return mock tool results."""
        if "web_search" in full_tool_name:
            query = arguments.get("query", "")
            return json.dumps([
                {"title": f"Mock result for '{query}'", "link": "https://example.com"}
            ])
        elif "read_file" in full_tool_name:
            path = arguments.get("path", "")
            return f"Mock content of file: {path}"
        elif "write_file" in full_tool_name:
            path = arguments.get("path", "")
            return f"Mock: File written to {path}"
        elif "search_repositories" in full_tool_name:
            query = arguments.get("query", "")
            return json.dumps([
                {"name": f"mock-repo", "full_name": f"user/mock-repo", "description": f"Mock repo for {query}"}
            ])
        return "Mock tool result"
    
    async def close(self) -> None:
        """No-op for mock client."""
        pass
