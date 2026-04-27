"""DeepSeek API client for LLM interactions."""

import json
from typing import Any, AsyncGenerator

import httpx
from openai import AsyncOpenAI

from a2a_mcp_agent.config import get_settings
from a2a_mcp_agent.utils.logging import get_logger

logger = get_logger(__name__)


class DeepSeekClient:
    """Client for DeepSeek API using OpenAI-compatible interface."""
    
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        """Initialize the DeepSeek client.
        
        Args:
            api_key: DeepSeek API key (optional, uses settings if not provided)
            base_url: API base URL (optional, uses settings if not provided)
        """
        settings = get_settings()
        self.api_key = api_key or settings.deepseek_api_key
        self.base_url = base_url or settings.deepseek_base_url
        self.model = settings.deepseek_model
        # Mock mode is on if the global toggle is set OR no api_key is available
        # via either the constructor or settings.
        self.mock_mode = settings.mock_mode or not self.api_key
        
        if not self.mock_mode and self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        else:
            self.client = None
            logger.info("DeepSeek client initialized in mock mode")
    
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Send a chat completion request.
        
        Args:
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions
            tool_choice: Tool choice strategy
            
        Returns:
            API response as dictionary
        """
        if self.mock_mode or not self.client:
            return self._mock_response(messages, tools)
        
        try:
            params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                params["max_tokens"] = max_tokens
            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice
            
            response = await self.client.chat.completions.create(**params)
            return response.model_dump()
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    async def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion response.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of the response text
        """
        if self.mock_mode or not self.client:
            # Mock streaming response
            mock_text = self._generate_mock_text(messages)
            words = mock_text.split()
            for word in words:
                yield word + " "
            return
        
        try:
            params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
            }
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            stream = await self.client.chat.completions.create(**params)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            raise
    
    def _mock_response(
        self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Generate mock response for testing."""
        last_message = messages[-1].get("content", "") if messages else ""
        
        # Check if this looks like a tool call request
        if tools and any(tool.get("type") == "function" for tool in tools):
            # Return a mock tool call
            return {
                "id": "mock-chat-completion",
                "object": "chat.completion",
                "created": 1234567890,
                "model": self.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "mock-tool-call-1",
                            "type": "function",
                            "function": {
                                "name": "web_search",
                                "arguments": json.dumps({"query": "mock search"}),
                            },
                        }],
                    },
                    "finish_reason": "tool_calls",
                }],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            }
        
        # Regular text response
        mock_content = self._generate_mock_text(messages)
        return {
            "id": "mock-chat-completion",
            "object": "chat.completion",
            "created": 1234567890,
            "model": self.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": mock_content,
                },
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }
    
    def _generate_mock_text(self, messages: list[dict[str, str]]) -> str:
        """Generate mock response text based on conversation."""
        last_message = messages[-1].get("content", "") if messages else ""
        
        if "search" in last_message.lower():
            return "I'll search for that information for you."
        elif "file" in last_message.lower():
            return "I'll help you with file operations."
        elif "github" in last_message.lower():
            return "I can help you search GitHub repositories."
        else:
            return f"This is a mock response from {self.model}. In production, this would be a real LLM response based on your query: '{last_message[:50]}...'"
    
    async def close(self) -> None:
        """Close the client connection."""
        if self.client:
            await self.client.close()
