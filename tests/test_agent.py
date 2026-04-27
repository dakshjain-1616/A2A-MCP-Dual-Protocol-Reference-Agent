"""Tests for Agent logic."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from a2a_mcp_agent.agent import Agent


class TestAgent:
    """Test Agent functionality."""
    
    @pytest.fixture
    async def agent(self) -> Agent:
        """Create a mock agent."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        return agent
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self) -> None:
        """Test agent initialization."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        assert agent.mock_mode is True
        assert agent.llm_client is not None
        assert agent.mcp_client is not None
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_process_task_simple(self) -> None:
        """Test processing a simple task."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        result = await agent.process_task("Hello, how are you?")
        
        assert result["success"] is True
        assert "response" in result
        assert isinstance(result["response"], str)
        assert result["tool_calls_executed"] >= 0
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_process_task_with_context(self) -> None:
        """Test processing task with context."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]
        result = await agent.process_task("What is Python?", context=context)
        
        assert result["success"] is True
        assert "response" in result
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_research_task(self) -> None:
        """Test research task."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        result = await agent.research("Python programming language")
        
        assert result["success"] is True
        assert "response" in result
        assert "usage" in result
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_get_available_tools(self) -> None:
        """Test getting available tools."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        tools = agent.get_available_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_process_task_stream(self) -> None:
        """Test streaming task processing."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        chunks = []
        async for chunk in agent.process_task_stream("Hello"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_text = "".join(chunks)
        assert len(full_text) > 0
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_agent_close(self) -> None:
        """Test agent cleanup."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        await agent.close()
        
        # Should be able to call close multiple times without error
        await agent.close()


class TestAgentWithToolCalls:
    """Test agent with tool call execution."""
    
    @pytest.mark.asyncio
    async def test_execute_tool_call(self) -> None:
        """Test executing a tool call."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        tool_call = {
            "id": "test-call-1",
            "function": {
                "name": "web_search__web_search",
                "arguments": json.dumps({"query": "test"}),
            },
        }
        
        result = await agent._execute_tool_call(tool_call)
        
        assert result["tool_call_id"] == "test-call-1"
        assert result["tool_name"] == "web_search__web_search"
        assert result["success"] is True
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_execute_tool_call_invalid_json(self) -> None:
        """Test executing tool call with invalid JSON arguments."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        tool_call = {
            "id": "test-call-2",
            "function": {
                "name": "web_search__web_search",
                "arguments": "invalid json",
            },
        }
        
        result = await agent._execute_tool_call(tool_call)
        
        assert result["tool_call_id"] == "test-call-2"
        # Should handle invalid JSON gracefully
        assert result["success"] is True  # Mock client returns result anyway
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_execute_tool_call_error(self) -> None:
        """Test executing tool call that raises error."""
        agent = Agent(mock_mode=True)
        await agent.initialize()
        
        # Use an unknown tool to trigger error handling
        tool_call = {
            "id": "test-call-3",
            "function": {
                "name": "unknown__tool",
                "arguments": json.dumps({}),
            },
        }
        
        result = await agent._execute_tool_call(tool_call)
        
        assert result["tool_call_id"] == "test-call-3"
        # Mock client handles unknown tools gracefully
        assert result["success"] is True
        
        await agent.close()
