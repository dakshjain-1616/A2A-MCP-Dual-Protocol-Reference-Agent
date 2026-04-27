"""A2A MCP Reference Agent - A production-ready dual-protocol agent."""

__version__ = "0.1.0"
__author__ = "Agent Developer"

from a2a_mcp_agent.agent import Agent
from a2a_mcp_agent.config import Settings, get_settings

__all__ = ["Agent", "Settings", "get_settings"]
