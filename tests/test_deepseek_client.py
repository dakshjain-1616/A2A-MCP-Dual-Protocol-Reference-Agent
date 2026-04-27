"""Tests for DeepSeek client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from a2a_mcp_agent.deepseek_client import DeepSeekClient


class TestDeepSeekClient:
    """Test DeepSeek client functionality."""
    
    @pytest.fixture
    def mock_client(self) -> DeepSeekClient:
        """Create a mock mode client."""
        return DeepSeekClient(api_key=None)
    
    @pytest.mark.asyncio
    async def test_mock_chat_completion(self, mock_client: DeepSeekClient) -> None:
        """Test mock chat completion."""
        messages = [{"role": "user", "content": "Hello"}]
        response = await mock_client.chat_completion(messages)
        
        assert "choices" in response
        assert len(response["choices"]) == 1
        assert response["choices"][0]["message"]["role"] == "assistant"
        assert "content" in response["choices"][0]["message"]
    
    @pytest.mark.asyncio
    async def test_mock_chat_completion_with_tools(self, mock_client: DeepSeekClient) -> None:
        """Test mock chat completion with tool calls."""
        messages = [{"role": "user", "content": "Search for something"}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]
        
        response = await mock_client.chat_completion(messages, tools=tools)
        
        assert "choices" in response
        message = response["choices"][0]["message"]
        assert "tool_calls" in message
    
    @pytest.mark.asyncio
    async def test_mock_streaming(self, mock_client: DeepSeekClient) -> None:
        """Test mock streaming response."""
        messages = [{"role": "user", "content": "Hello"}]
        chunks = []
        
        async for chunk in mock_client.stream_chat_completion(messages):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        # Should receive multiple chunks
        full_text = "".join(chunks)
        assert len(full_text) > 0
    
    @pytest.mark.asyncio
    async def test_mock_response_generation(self, mock_client: DeepSeekClient) -> None:
        """Test mock response text generation."""
        # Test search-related query
        messages = [{"role": "user", "content": "search for python"}]
        response = await mock_client.chat_completion(messages)
        content = response["choices"][0]["message"]["content"]
        assert "search" in content.lower()
        
        # Test file-related query
        messages = [{"role": "user", "content": "read file"}]
        response = await mock_client.chat_completion(messages)
        content = response["choices"][0]["message"]["content"]
        assert "file" in content.lower()
        
        # Test github-related query
        messages = [{"role": "user", "content": "github repositories"}]
        response = await mock_client.chat_completion(messages)
        content = response["choices"][0]["message"]["content"]
        assert "github" in content.lower()
    
    def test_client_initialization_mock_mode(self) -> None:
        """Test client initialization in mock mode."""
        client = DeepSeekClient(api_key=None)
        assert client.mock_mode is True
        assert client.client is None
    
    @pytest.mark.asyncio
    async def test_usage_in_mock_response(self, mock_client: DeepSeekClient) -> None:
        """Test that mock responses include usage info."""
        messages = [{"role": "user", "content": "Hello"}]
        response = await mock_client.chat_completion(messages)
        
        assert "usage" in response
        assert "prompt_tokens" in response["usage"]
        assert "completion_tokens" in response["usage"]
        assert "total_tokens" in response["usage"]


class TestDeepSeekClientReal:
    """Test DeepSeek client with mocked real API calls."""
    
    @pytest.mark.asyncio
    @patch("a2a_mcp_agent.deepseek_client.AsyncOpenAI")
    async def test_real_client_initialization(self, mock_openai: MagicMock) -> None:
        """Test real client initialization."""
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        
        client = DeepSeekClient(api_key="test-key")
        assert client.mock_mode is False
        assert client.client is not None
    
    @pytest.mark.asyncio
    @patch("a2a_mcp_agent.deepseek_client.AsyncOpenAI")
    async def test_chat_completion_with_real_client(self, mock_openai: MagicMock) -> None:
        """Test chat completion with mocked real client."""
        # Setup mock
        mock_instance = MagicMock()
        mock_chat = AsyncMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 100},
        }
        mock_chat.return_value = mock_response
        mock_instance.chat.completions.create = mock_chat
        mock_openai.return_value = mock_instance
        
        client = DeepSeekClient(api_key="test-key")
        messages = [{"role": "user", "content": "Hello"}]
        
        response = await client.chat_completion(messages)
        
        assert response["choices"][0]["message"]["content"] == "Test response"
        mock_chat.assert_called_once()
