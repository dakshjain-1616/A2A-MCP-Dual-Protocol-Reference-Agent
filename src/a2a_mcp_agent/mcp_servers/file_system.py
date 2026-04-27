"""File System MCP Server - Provides file system operations."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from a2a_mcp_agent.utils.logging import get_logger

logger = get_logger(__name__)

# Server instance
server = Server("file-system-server")

# Base directory for file operations (configurable)
BASE_DIR = Path(os.environ.get("MCP_FILE_BASE_DIR", "/tmp/mcp_files"))
BASE_DIR.mkdir(parents=True, exist_ok=True)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available file system tools."""
    return [
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write",
                    },
                },
                "required": ["path", "content"],
            },
        ),
        Tool(
            name="list_directory",
            description="List contents of a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the directory (default: root)",
                        "default": ".",
                    },
                },
            },
        ),
        Tool(
            name="delete_file",
            description="Delete a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file",
                    },
                },
                "required": ["path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name == "read_file":
        return await _handle_read_file(arguments)
    elif name == "write_file":
        return await _handle_write_file(arguments)
    elif name == "list_directory":
        return await _handle_list_directory(arguments)
    elif name == "delete_file":
        return await _handle_delete_file(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


def _resolve_path(rel_path: str) -> Path:
    """Resolve relative path to absolute path within base directory."""
    # Prevent directory traversal attacks
    abs_path = (BASE_DIR / rel_path).resolve()
    if not str(abs_path).startswith(str(BASE_DIR)):
        raise ValueError("Path traversal detected")
    return abs_path


async def _handle_read_file(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle read file tool call."""
    rel_path = arguments.get("path", "")
    
    try:
        file_path = _resolve_path(rel_path)
        if not file_path.exists():
            return [TextContent(type="text", text=f"Error: File not found: {rel_path}")]
        
        content = file_path.read_text(encoding="utf-8")
        return [TextContent(type="text", text=content)]
    except Exception as e:
        logger.error(f"Read file error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_write_file(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle write file tool call."""
    rel_path = arguments.get("path", "")
    content = arguments.get("content", "")
    
    try:
        file_path = _resolve_path(rel_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return [TextContent(type="text", text=f"File written successfully: {rel_path}")]
    except Exception as e:
        logger.error(f"Write file error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_list_directory(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle list directory tool call."""
    rel_path = arguments.get("path", ".")
    
    try:
        dir_path = _resolve_path(rel_path)
        if not dir_path.exists():
            return [TextContent(type="text", text=f"Error: Directory not found: {rel_path}")]
        
        if not dir_path.is_dir():
            return [TextContent(type="text", text=f"Error: Not a directory: {rel_path}")]
        
        entries = []
        for item in dir_path.iterdir():
            entry_type = "directory" if item.is_dir() else "file"
            size = item.stat().st_size if item.is_file() else None
            entries.append({
                "name": item.name,
                "type": entry_type,
                "size": size,
            })
        
        return [TextContent(type="text", text=json.dumps(entries, indent=2))]
    except Exception as e:
        logger.error(f"List directory error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_delete_file(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle delete file tool call."""
    rel_path = arguments.get("path", "")
    
    try:
        file_path = _resolve_path(rel_path)
        if not file_path.exists():
            return [TextContent(type="text", text=f"Error: File not found: {rel_path}")]
        
        if file_path.is_dir():
            return [TextContent(type="text", text=f"Error: Cannot delete directory: {rel_path}")]
        
        file_path.unlink()
        return [TextContent(type="text", text=f"File deleted: {rel_path}")]
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


class FileSystemServer:
    """File System MCP Server wrapper."""
    
    def __init__(self, base_dir: str = "/tmp/mcp_files") -> None:
        """Initialize the server."""
        self.name = "file-system-server"
        global BASE_DIR
        BASE_DIR = Path(base_dir)
        BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    async def run(self) -> None:
        """Run the server."""
        async with stdio_server(server) as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Main entry point."""
    server_instance = FileSystemServer()
    asyncio.run(server_instance.run())


if __name__ == "__main__":
    main()
