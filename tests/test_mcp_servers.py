"""Tests for MCP servers."""

import json
import tempfile
from pathlib import Path

import pytest

from a2a_mcp_agent.mcp_servers.file_system import FileSystemServer, _resolve_path, BASE_DIR
from a2a_mcp_agent.mcp_servers.web_search import WebSearchServer
from a2a_mcp_agent.mcp_servers.github import GitHubServer


class TestWebSearchServer:
    """Test Web Search MCP Server."""

    def test_server_initialization(self) -> None:
        """Test server initialization."""
        server = WebSearchServer()
        assert server.name == "web-search-server"

    def test_server_has_required_methods(self) -> None:
        """Test server has required methods."""
        server = WebSearchServer()
        assert hasattr(server, "list_tools")
        assert hasattr(server, "call_tool")


class TestFileSystemServer:
    """Test File System MCP Server."""

    def test_server_initialization(self) -> None:
        """Test server initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            server = FileSystemServer(base_dir=tmpdir)
            assert server.name == "file-system-server"
            assert Path(tmpdir).exists()

    def test_resolve_path(self) -> None:
        """Test path resolution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create server with temp directory
            server = FileSystemServer(base_dir=tmpdir)
            # Test that the server resolves paths correctly
            resolved = server._resolve_path("test.txt")
            assert resolved == Path(tmpdir) / "test.txt"

    def test_resolve_path_traversal_prevention(self) -> None:
        """Test path traversal prevention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            server = FileSystemServer(base_dir=tmpdir)
            with pytest.raises(ValueError, match="Path traversal"):
                server._resolve_path("../etc/passwd")

    def test_server_has_required_methods(self) -> None:
        """Test server has required methods."""
        server = FileSystemServer()
        assert hasattr(server, "list_tools")
        assert hasattr(server, "call_tool")


class TestGitHubServer:
    """Test GitHub MCP Server."""

    def test_server_initialization(self) -> None:
        """Test server initialization."""
        server = GitHubServer()
        assert server.name == "github-server"

    def test_server_has_required_methods(self) -> None:
        """Test server has required methods."""
        server = GitHubServer()
        assert hasattr(server, "list_tools")
        assert hasattr(server, "call_tool")


class TestMCPServerTools:
    """Test MCP server tool definitions."""

    def test_web_search_tools_structure(self) -> None:
        """Test web search tools have correct structure."""
        # Import the server module to check tool definitions
        from a2a_mcp_agent.mcp_servers.web_search import list_tools

        # Note: list_tools is decorated, so we can't call it directly without async
        # This test verifies the module structure
        assert callable(list_tools)

    def test_file_system_tools_structure(self) -> None:
        """Test file system tools have correct structure."""
        from a2a_mcp_agent.mcp_servers.file_system import list_tools

        assert callable(list_tools)

    def test_github_tools_structure(self) -> None:
        """Test GitHub tools have correct structure."""
        from a2a_mcp_agent.mcp_servers.github import list_tools

        assert callable(list_tools)


class TestMCPServerIntegration:
    """Test MCP server integration."""

    @pytest.mark.asyncio
    async def test_web_search_mock_response(self) -> None:
        """Test web search mock response."""
        from a2a_mcp_agent.mcp_servers.web_search import _handle_web_search

        class MockSettings:
            is_mock_mode = True
            serper_api_key = None

        arguments = {"query": "python", "num_results": 3}
        result = await _handle_web_search(arguments, MockSettings())

        assert len(result) == 1
        assert result[0].type == "text"

        # Parse JSON response - web_search returns a list directly
        data = json.loads(result[0].text)
        assert isinstance(data, list)
        assert len(data) <= 3
        # Each item should have title, link, snippet
        for item in data:
            assert "title" in item
            assert "link" in item
            assert "snippet" in item

    @pytest.mark.asyncio
    async def test_file_system_read_mock(self) -> None:
        """Test file system read operation."""
        from a2a_mcp_agent.mcp_servers.file_system import _handle_read_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, World!")

            # Create server with temp directory
            server = FileSystemServer(base_dir=tmpdir)
            result = await server._handle_read_file({"path": "test.txt"})

            assert len(result) == 1
            assert result[0].type == "text"
            assert "Hello, World!" in result[0].text

    @pytest.mark.asyncio
    async def test_file_system_write_mock(self) -> None:
        """Test file system write operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create server with temp directory
            server = FileSystemServer(base_dir=tmpdir)
            result = await server._handle_write_file({
                "path": "output.txt",
                "content": "Test content",
            })

            assert len(result) == 1
            assert result[0].type == "text"
            assert "successfully" in result[0].text

            # Verify file was created
            assert (Path(tmpdir) / "output.txt").exists()

    @pytest.mark.asyncio
    async def test_github_mock_search(self) -> None:
        """Test GitHub search mock response."""
        from a2a_mcp_agent.mcp_servers.github import _handle_search_repositories

        class MockSettings:
            is_mock_mode = True
            github_token = None

        arguments = {"query": "python", "per_page": 5}
        result = await _handle_search_repositories(arguments, MockSettings())

        assert len(result) == 1
        assert result[0].type == "text"

        # Parse JSON response - github returns a dict with total_count and items
        data = json.loads(result[0].text)
        assert isinstance(data, dict)
        assert "total_count" in data
        assert "items" in data
        assert isinstance(data["items"], list)
