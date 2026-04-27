"""A2A Protocol Server - FastAPI implementation of A2A protocol."""

import json
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from a2a_mcp_agent.agent import Agent
from a2a_mcp_agent.config import get_settings
from a2a_mcp_agent.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

# Global agent instance
agent: Agent | None = None


# Pydantic models for A2A protocol
class TaskRequest(BaseModel):
    """A2A task request."""
    id: str = Field(..., description="Unique task ID")
    session_id: str | None = Field(None, description="Session ID for conversation context")
    message: dict[str, Any] = Field(..., description="User message")
    context: list[dict[str, Any]] = Field(default_factory=list, description="Conversation context")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TaskResponse(BaseModel):
    """A2A task response."""
    id: str = Field(..., description="Task ID")
    session_id: str | None = Field(None, description="Session ID")
    status: str = Field(..., description="Task status")
    result: dict[str, Any] | None = Field(None, description="Task result")
    error: dict[str, Any] | None = Field(None, description="Error details if failed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentCard(BaseModel):
    """A2A Agent Card."""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    url: str = Field(..., description="Agent URL")
    version: str = Field(..., description="Agent version")
    capabilities: dict[str, Any] = Field(..., description="Agent capabilities")
    skills: list[dict[str, Any]] = Field(..., description="Agent skills")
    default_input_modes: list[str] = Field(default_factory=lambda: ["text"])
    default_output_modes: list[str] = Field(default_factory=lambda: ["text"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global agent
    
    # Startup
    setup_logging()
    settings = get_settings()
    logger.info("Starting A2A server...")
    
    agent = Agent(mock_mode=settings.is_mock_mode)
    await agent.initialize()
    logger.info("Agent initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down A2A server...")
    if agent:
        await agent.close()


# Create FastAPI app
app = FastAPI(
    title="A2A MCP Reference Agent",
    description="A2A Protocol server with MCP tool integration",
    version="0.1.0",
    lifespan=lifespan,
)


def get_agent_card() -> dict[str, Any]:
    """Get agent card configuration."""
    settings = get_settings()
    
    # Get available tools
    tools = []
    if agent:
        try:
            tools = agent.get_available_tools()
        except Exception as e:
            logger.warning(f"Could not get tools: {e}")
    
    return {
        "name": "A2A MCP Reference Agent",
        "description": "A production-ready dual-protocol agent supporting A2A and MCP protocols with DeepSeek LLM integration",
        "url": f"http://{settings.a2a_host}:{settings.a2a_port}",
        "version": "0.1.0",
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionCallback": False,
        },
        "skills": [
            {
                "id": "research",
                "name": "Research Assistant",
                "description": "Performs research using web search and GitHub",
            },
            {
                "id": "file_operations",
                "name": "File Operations",
                "description": "Read, write, and manage files",
            },
        ],
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "tools": [
            {
                "name": tool.get("name"),
                "description": tool.get("description"),
            }
            for tool in tools
        ],
    }


@app.get("/.well-known/agent-card.json")
async def get_agent_card_endpoint() -> JSONResponse:
    """Serve agent card."""
    return JSONResponse(content=get_agent_card())


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "name": "A2A MCP Reference Agent",
        "version": "0.1.0",
        "status": "healthy",
        "protocols": ["A2A", "MCP"],
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "agent": "ready" if agent else "not_initialized"}


@app.post("/tasks/send", response_model=TaskResponse)
async def send_task(request: TaskRequest) -> TaskResponse:
    """Send a task to the agent."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Extract message content
        message_content = request.message.get("content", "")
        if not message_content:
            raise HTTPException(status_code=400, detail="Message content is required")
        
        # Process task
        result = await agent.process_task(
            task=message_content,
            context=request.context if request.context else None,
        )
        
        return TaskResponse(
            id=request.id,
            session_id=request.session_id,
            status="completed",
            result={
                "content": result.get("response", ""),
                "tool_calls": result.get("tool_calls_executed", 0),
            },
            metadata={
                "usage": result.get("usage", {}),
                "tool_results": result.get("tool_results", []),
            },
        )
    except Exception as e:
        logger.error(f"Task processing error: {e}")
        return TaskResponse(
            id=request.id,
            session_id=request.session_id,
            status="failed",
            error={"message": str(e)},
        )


@app.post("/tasks/sendSubscribe")
async def send_task_subscribe(request: TaskRequest) -> StreamingResponse:
    """Send a task with streaming response."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        try:
            message_content = request.message.get("content", "")
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'status': 'working'})}\n\n"
            
            # Stream response chunks
            async for chunk in agent.process_task_stream(message_content):
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            
            # Send completion
            yield f"data: {json.dumps({'type': 'status', 'status': 'completed'})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/tasks/{task_id}")
async def get_task(task_id: str) -> TaskResponse:
    """Get task status (simplified - returns not found)."""
    return TaskResponse(
        id=task_id,
        status="unknown",
        metadata={"message": "Task history not implemented in this version"},
    )


@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str) -> TaskResponse:
    """Cancel a task (simplified)."""
    return TaskResponse(
        id=task_id,
        status="cancelled",
        metadata={"message": "Task cancellation not fully implemented"},
    )


def main() -> None:
    """Main entry point."""
    import uvicorn
    
    settings = get_settings()
    
    # Create agent card file
    card_path = os.path.join(os.path.dirname(__file__), "agent-card.json")
    with open(card_path, "w") as f:
        json.dump(get_agent_card(), f, indent=2)
    
    logger.info(f"Starting A2A server on {settings.a2a_host}:{settings.a2a_port}")
    
    uvicorn.run(
        "a2a_mcp_agent.a2a_server:app",
        host=settings.a2a_host,
        port=settings.a2a_port,
        reload=settings.a2a_debug,
    )


if __name__ == "__main__":
    main()
