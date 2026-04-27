# A2A MCP Reference Agent Makefile
.PHONY: help install dev-install test lint format clean serve-a2a serve-mcp serve-ui serve-all docker-build docker-run

# Default target
help:
	@echo "A2A MCP Reference Agent - Available Commands:"
	@echo ""
	@echo "  Setup:"
	@echo "    make install        - Install production dependencies"
	@echo "    make dev-install    - Install with dev dependencies"
	@echo ""
	@echo "  Development:"
	@echo "    make test           - Run pytest suite"
	@echo "    make test-cov       - Run tests with coverage"
	@echo "    make lint           - Run ruff and mypy"
	@echo "    make format         - Auto-format code with ruff"
	@echo ""
	@echo "  Services:"
	@echo "    make serve-a2a      - Start A2A server (port 8000)"
	@echo "    make serve-mcp      - Start MCP servers"
	@echo "    make serve-ui       - Start Gradio UI (port 7860)"
	@echo "    make serve-mock     - Start all services in mock mode"
	@echo "    make serve-all      - Start all services"
	@echo ""
	@echo "  Utilities:"
	@echo "    make clean          - Remove build artifacts"
	@echo "    make docker-build   - Build Docker image"
	@echo "    make docker-run     - Run Docker container"

# Installation
install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src/a2a_mcp_agent --cov-report=term-missing

# Linting and formatting
lint:
	ruff check src/ tests/
	mypy src/a2a_mcp_agent

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# Service targets
serve-a2a:
	python -m a2a_mcp_agent.a2a_server

serve-mcp:
	@echo "Starting MCP servers..."
	python -m a2a_mcp_agent.mcp_servers.web_search &
	python -m a2a_mcp_agent.mcp_servers.file_system &
	python -m a2a_mcp_agent.mcp_servers.github &

serve-ui:
	python -m a2a_mcp_agent.ui

serve-mock:
	@echo "Starting all services in mock mode..."
	@echo "A2A Server: http://localhost:8000"
	@echo "Gradio UI: http://localhost:7860"
	python -m a2a_mcp_agent.a2a_server --mock &
	python -m a2a_mcp_agent.ui &
	wait

serve-all:
	@echo "Starting all services..."
	python -m a2a_mcp_agent.a2a_server &
	python -m a2a_mcp_agent.ui &
	wait

# Cleanup
clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker
docker-build:
	docker build -t a2a-mcp-agent:latest .

docker-run:
	docker run -p 8000:8000 -p 7860:7860 --env-file .env a2a-mcp-agent:latest
