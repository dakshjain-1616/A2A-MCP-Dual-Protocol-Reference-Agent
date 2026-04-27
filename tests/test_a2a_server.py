"""Tests for A2A server."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from a2a_mcp_agent.a2a_server import app, get_agent_card


class TestA2AServer:
    """Test A2A server endpoints."""
    
    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)
    
    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "A2A MCP Reference Agent"
        assert data["version"] == "0.1.0"
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self, client: TestClient) -> None:
        """Test health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_agent_card_endpoint(self, client: TestClient) -> None:
        """Test agent card endpoint."""
        response = client.get("/.well-known/agent-card.json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "description" in data
        assert "url" in data
        assert "version" in data
        assert "capabilities" in data
        assert "skills" in data
    
    def test_agent_card_content(self, client: TestClient) -> None:
        """Test agent card content structure."""
        response = client.get("/.well-known/agent-card.json")
        data = response.json()
        
        assert data["name"] == "A2A MCP Reference Agent"
        assert "A2A" in data["capabilities"]
        assert isinstance(data["skills"], list)
        assert len(data["skills"]) > 0
        
        # Check skills structure
        for skill in data["skills"]:
            assert "id" in skill
            assert "name" in skill
            assert "description" in skill
    
    @patch("a2a_mcp_agent.a2a_server.agent")
    def test_send_task_endpoint(self, mock_agent: MagicMock, client: TestClient) -> None:
        """Test task sending endpoint."""
        # Setup mock agent
        mock_agent_instance = MagicMock()
        mock_agent_instance.process_task = AsyncMock(return_value={
            "success": True,
            "response": "Test response",
            "tool_calls_executed": 0,
            "tool_results": [],
            "usage": {"total_tokens": 100},
        })
        mock_agent_instance.get_available_tools = MagicMock(return_value=[])
        mock_agent.return_value = mock_agent_instance
        
        task_request = {
            "id": "test-task-1",
            "message": {"role": "user", "content": "Hello"},
        }
        
        response = client.post("/tasks/send", json=task_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-task-1"
        assert data["status"] == "completed"
        assert "result" in data
    
    @patch("a2a_mcp_agent.a2a_server.agent")
    def test_send_task_with_context(self, mock_agent: MagicMock, client: TestClient) -> None:
        """Test task sending with context."""
        mock_agent_instance = MagicMock()
        mock_agent_instance.process_task = AsyncMock(return_value={
            "success": True,
            "response": "Test response with context",
            "tool_calls_executed": 0,
            "tool_results": [],
            "usage": {},
        })
        mock_agent_instance.get_available_tools = MagicMock(return_value=[])
        mock_agent.return_value = mock_agent_instance
        
        task_request = {
            "id": "test-task-2",
            "session_id": "session-123",
            "message": {"role": "user", "content": "Hello"},
            "context": [{"role": "system", "content": "You are helpful"}],
        }
        
        response = client.post("/tasks/send", json=task_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session-123"
    
    def test_send_task_missing_content(self, client: TestClient) -> None:
        """Test task sending with missing content."""
        task_request = {
            "id": "test-task-3",
            "message": {"role": "user"},  # Missing content
        }
        
        response = client.post("/tasks/send", json=task_request)
        
        assert response.status_code == 400
        assert "content is required" in response.json()["detail"].lower()
    
    def test_get_task_endpoint(self, client: TestClient) -> None:
        """Test get task endpoint."""
        response = client.get("/tasks/test-task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-task-123"
        assert data["status"] == "unknown"
    
    def test_cancel_task_endpoint(self, client: TestClient) -> None:
        """Test cancel task endpoint."""
        response = client.post("/tasks/test-task-123/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-task-123"
        assert data["status"] == "cancelled"
    
    def test_get_agent_card_function(self) -> None:
        """Test get_agent_card function."""
        card = get_agent_card()
        
        assert isinstance(card, dict)
        assert "name" in card
        assert "description" in card
        assert "url" in card
        assert "version" in card
        assert "capabilities" in card
        assert "skills" in card


class TestA2AServerStreaming:
    """Test A2A server streaming endpoints."""
    
    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)
    
    @patch("a2a_mcp_agent.a2a_server.agent")
    def test_send_task_subscribe(self, mock_agent: MagicMock, client: TestClient) -> None:
        """Test streaming task endpoint."""
        # Setup mock agent
        mock_agent_instance = MagicMock()
        
        async def mock_stream(*args, **kwargs):
            yield "Hello"
            yield " "
            yield "World"
        
        mock_agent_instance.process_task_stream = mock_stream
        mock_agent_instance.get_available_tools = MagicMock(return_value=[])
        mock_agent.return_value = mock_agent_instance
        
        task_request = {
            "id": "stream-task-1",
            "message": {"role": "user", "content": "Hello"},
        }
        
        response = client.post("/tasks/sendSubscribe", json=task_request)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Check that we got SSE data
        content = response.content.decode()
        assert "data:" in content


class TestA2AProtocolCompliance:
    """Test A2A protocol compliance."""
    
    def test_agent_card_has_required_fields(self) -> None:
        """Test that agent card has all required A2A fields."""
        card = get_agent_card()
        
        required_fields = [
            "name",
            "description",
            "url",
            "version",
            "capabilities",
            "skills",
            "defaultInputModes",
            "defaultOutputModes",
        ]
        
        for field in required_fields:
            assert field in card, f"Missing required field: {field}"
    
    def test_capabilities_structure(self) -> None:
        """Test capabilities structure."""
        card = get_agent_card()
        capabilities = card["capabilities"]
        
        assert isinstance(capabilities, dict)
        assert "streaming" in capabilities
    
    def test_skills_structure(self) -> None:
        """Test skills structure."""
        card = get_agent_card()
        skills = card["skills"]
        
        assert isinstance(skills, list)
        assert len(skills) > 0
        
        for skill in skills:
            assert "id" in skill
            assert "name" in skill
            assert "description" in skill
