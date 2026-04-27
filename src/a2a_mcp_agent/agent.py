"""Agent logic - Reasoning loop connecting LLM to MCP tools."""

import json
from typing import Any, AsyncGenerator

from a2a_mcp_agent.config import get_settings
from a2a_mcp_agent.deepseek_client import DeepSeekClient
from a2a_mcp_agent.mcp_client import MCPClient, MockMCPClient
from a2a_mcp_agent.utils.logging import get_logger

logger = get_logger(__name__)


class Agent:
    """Main agent class that orchestrates LLM and MCP tools."""
    
    def __init__(self, mock_mode: bool = False) -> None:
        """Initialize the agent.
        
        Args:
            mock_mode: Whether to run in mock mode without real API calls
        """
        self.settings = get_settings()
        self.mock_mode = mock_mode or self.settings.is_mock_mode
        
        # Initialize clients
        self.llm_client = DeepSeekClient()
        self.mcp_client = MockMCPClient() if self.mock_mode else MCPClient()
        
        logger.info(f"Agent initialized (mock_mode={self.mock_mode})")
    
    async def initialize(self) -> None:
        """Initialize MCP connections."""
        await self.mcp_client.connect_all_servers()
        logger.info("Agent MCP connections established")
    
    async def process_task(
        self, task: str, context: list[dict[str, str]] | None = None
    ) -> dict[str, Any]:
        """Process a task using LLM and available tools.
        
        Args:
            task: The task description or user query
            context: Optional conversation context
            
        Returns:
            Task result with response and metadata
        """
        messages = context or []
        messages.append({"role": "user", "content": task})
        
        # Get available tools
        tools = self.mcp_client.get_tools_for_llm()
        
        # Call LLM with tools
        response = await self.llm_client.chat_completion(
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
        )
        
        # Extract message from response
        choice = response["choices"][0]
        message = choice["message"]
        
        # Check if tool calls are needed
        tool_calls = message.get("tool_calls", [])
        
        if tool_calls:
            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                result = await self._execute_tool_call(tool_call)
                tool_results.append(result)
            
            # Add tool results to messages and get final response
            messages.append(message)
            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": result["tool_call_id"],
                    "content": result["content"],
                })
            
            # Get final response from LLM
            final_response = await self.llm_client.chat_completion(
                messages=messages,
                tools=None,
            )
            
            final_message = final_response["choices"][0]["message"]
            return {
                "success": True,
                "response": final_message.get("content", ""),
                "tool_calls_executed": len(tool_results),
                "tool_results": tool_results,
                "usage": final_response.get("usage", {}),
            }
        
        # No tool calls, return direct response
        return {
            "success": True,
            "response": message.get("content", ""),
            "tool_calls_executed": 0,
            "tool_results": [],
            "usage": response.get("usage", {}),
        }
    
    async def process_task_stream(
        self, task: str, context: list[dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        """Process a task with streaming response.
        
        Args:
            task: The task description or user query
            context: Optional conversation context
            
        Yields:
            Response chunks
        """
        messages = context or []
        messages.append({"role": "user", "content": task})
        
        # For streaming, we simplify and don't do tool calls
        # In production, you'd handle this more carefully
        async for chunk in self.llm_client.stream_chat_completion(messages=messages):
            yield chunk
    
    async def _execute_tool_call(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        """Execute a single tool call.
        
        Args:
            tool_call: Tool call from LLM
            
        Returns:
            Tool execution result
        """
        tool_id = tool_call.get("id", "unknown")
        function = tool_call.get("function", {})
        tool_name = function.get("name", "")
        arguments_str = function.get("arguments", "{}")
        
        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            arguments = {}
        
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")
        
        try:
            result = await self.mcp_client.call_tool_by_full_name(tool_name, arguments)
            return {
                "tool_call_id": tool_id,
                "tool_name": tool_name,
                "success": True,
                "content": result,
            }
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "tool_call_id": tool_id,
                "tool_name": tool_name,
                "success": False,
                "content": f"Error: {str(e)}",
            }
    
    async def research(
        self, query: str, use_web_search: bool = True, use_github: bool = True
    ) -> dict[str, Any]:
        """Perform a research task using available tools.
        
        Args:
            query: Research query
            use_web_search: Whether to use web search
            use_github: Whether to use GitHub search
            
        Returns:
            Research results
        """
        task_parts = [f"Research the following topic: {query}"]
        
        if use_web_search:
            task_parts.append("Use web_search to find relevant information.")
        if use_github:
            task_parts.append("Use github search_repositories to find relevant repositories.")
        
        task_parts.append("Provide a comprehensive summary of your findings.")
        
        full_task = " ".join(task_parts)
        return await self.process_task(full_task)
    
    def get_available_tools(self) -> list[dict[str, Any]]:
        """Get list of available tools.
        
        Returns:
            List of tool definitions
        """
        return self.mcp_client.get_all_tools()
    
    async def close(self) -> None:
        """Clean up resources."""
        await self.mcp_client.close()
        await self.llm_client.close()
        logger.info("Agent resources cleaned up")
