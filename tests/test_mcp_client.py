"""Tests for MCP client."""

import json

import pytest

from a2a_mcp_agent.mcp_client import MockMCPClient


class TestMockMCPClient:
    """Test Mock MCP client functionality."""
    
    @pytest.fixture
    def mock_client(self) -> MockMCPClient:
        """Create a mock MCP client."""
        return MockMCPClient()
    
    @pytest.mark.asyncio
    async def test_connect_all_servers(self, mock_client: MockMCPClient) -> None:
        """Test connecting to all servers."""
        await mock_client.connect_all_servers()
        # Should not raise any exceptions
        assert True
    
    def test_get_all_tools(self, mock_client: MockMCPClient) -> None:
        """Test getting all tools."""
        tools = mock_client.get_all_tools()
        
        assert len(tools) > 0
        # Check that tools have expected structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "server" in tool
            assert "original_name" in tool
    
    def test_get_tools_for_llm(self, mock_client: MockMCPClient) -> None:
        """Test getting tools formatted for LLM."""
        tools = mock_client.get_tools_for_llm()
        
        assert len(tools) > 0
        # Check OpenAI format
        for tool in tools:
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]
    
    @pytest.mark.asyncio
    async def test_call_web_search_tool(self, mock_client: MockMCPClient) -> None:
        """Test calling web search tool."""
        result = await mock_client.call_tool_by_full_name(
            "web_search__web_search",
            {"query": "python programming"},
        )
        
        assert "mock" in result.lower() or "result" in result.lower()
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_call_file_read_tool(self, mock_client: MockMCPClient) -> None:
        """Test calling file read tool."""
        result = await mock_client.call_tool_by_full_name(
            "file_system__read_file",
            {"path": "/test/file.txt"},
        )
        
        assert "mock" in result.lower()
        assert "/test/file.txt" in result
    
    @pytest.mark.asyncio
    async def test_call_file_write_tool(self, mock_client: MockMCPClient) -> None:
        """Test calling file write tool."""
        result = await mock_client.call_tool_by_full_name(
            "file_system__write_file",
            {"path": "/test/output.txt", "content": "Hello"},
        )
        
        assert "mock" in result.lower() or "written" in result.lower()
    
    @pytest.mark.asyncio
    async def test_call_github_search_tool(self, mock_client: MockMCPClient) -> None:
        """Test calling GitHub search tool."""
        result = await mock_client.call_tool_by_full_name(
            "github__search_repositories",
            {"query": "python web framework"},
        )
        
        assert "mock" in result.lower() or "repo" in result.lower()
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_call_unknown_tool(self, mock_client: MockMCPClient) -> None:
        """Test calling unknown tool."""
        result = await mock_client.call_tool_by_full_name(
            "unknown__tool",
            {},
        )
        
        assert "mock tool result" in result.lower()
    
    @pytest.mark.asyncio
    async def test_close(self, mock_client: MockMCPClient) -> None:
        """Test closing the client."""
        await mock_client.close()
        # Should not raise any exceptions
        assert True
    
    def test_tool_prefix_format(self, mock_client: MockMCPClient) -> None:
        """Test that tool names are properly prefixed."""
        tools = mock_client.get_all_tools()
        
        for tool in tools:
            name = tool["name"]
            assert "__" in name
            parts = name.split("__")
            assert len(parts) == 2
            assert parts[0] in ["web_search", "file_system", "github"]
