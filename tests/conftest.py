"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

from a2a_mcp_agent.agent import Agent
from a2a_mcp_agent.config import Settings, get_settings
from a2a_mcp_agent.deepseek_client import DeepSeekClient
from a2a_mcp_agent.mcp_client import MockMCPClient


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    return Settings(
        deepseek_api_key=None,
        deepseek_base_url="https://api.deepseek.com/v1",
        deepseek_model="deepseek-v4-flash",
        mock_mode=True,
        a2a_host="127.0.0.1",
        a2a_port=8000,
        gradio_host="127.0.0.1",
        gradio_port=7860,
        log_level="DEBUG",
    )


@pytest_asyncio.fixture
async def mock_agent() -> AsyncGenerator[Agent, None]:
    """Create a mock agent for testing."""
    agent = Agent(mock_mode=True)
    await agent.initialize()
    yield agent
    await agent.close()


@pytest.fixture
def mock_deepseek_client() -> DeepSeekClient:
    """Create a mock DeepSeek client."""
    return DeepSeekClient(api_key=None)


@pytest.fixture
def mock_mcp_client() -> MockMCPClient:
    """Create a mock MCP client."""
    return MockMCPClient()
