# A2A MCP Reference Agent

A production-ready dual-protocol reference agent implementing both **A2A (Agent-to-Agent)** and **MCP (Model Context Protocol)** protocols with DeepSeek LLM integration.

## 🚀 Features

- **Dual Protocol Support**: Implements both A2A and MCP protocols
- **DeepSeek Integration**: Uses deepseek-v4-flash for LLM capabilities
- **MCP Servers**: Web Search, File System, and GitHub stdio servers
- **A2A Protocol**: FastAPI-based server with agent card and task endpoints
- **Gradio UI**: Three-panel dashboard for real-time monitoring
- **CLI Interface**: Rich command-line interface for all operations
- **Mock Mode**: Test without API keys
- **Full Test Suite**: 10+ pytest tests with coverage

## 📁 Project Structure

```
a2a-mcp-reference-agent/
├── src/a2a_mcp_agent/
│   ├── __init__.py
│   ├── agent.py              # Core agent logic
│   ├── a2a_server.py         # A2A FastAPI server
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration management
│   ├── deepseek_client.py   # DeepSeek API client
│   ├── mcp_client.py        # MCP client orchestrator
│   ├── ui.py                # Gradio dashboard
│   ├── mcp_servers/         # MCP stdio servers
│   │   ├── web_search.py
│   │   ├── file_system.py
│   │   └── github.py
│   └── utils/
│       └── logging.py
├── tests/                    # Test suite
├── docs/                     # Documentation
├── pyproject.toml
├── requirements.txt
├── Makefile
└── .env.example
```

## 🛠️ Installation

```bash
# Clone the repository
git clone <repository-url>
cd a2a-mcp-reference-agent

# Install dependencies
make dev-install

# Or with pip
pip install -e ".[dev]"
```

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required for real LLM calls
DEEPSEEK_API_KEY=your_api_key_here

# Optional API keys
GITHUB_TOKEN=your_github_token
SERPER_API_KEY=your_serper_api_key

# Run in mock mode (no API keys needed)
MOCK_MODE=true
```

## 🚀 Usage

### Start All Services

```bash
# Start in mock mode (no API keys required)
make serve-mock

# Or start services individually
make serve-a2a    # A2A server on port 8000
make serve-ui      # Gradio UI on port 7860
```

### CLI Commands

```bash
# Interactive chat mode
a2a-mcp-agent interactive

# Single message
a2a-mcp-agent chat "Hello, how are you?"

# Research task
a2a-mcp-agent research -q "Python web frameworks"

# Check status
a2a-mcp-agent status

# List tools
a2a-mcp-agent tools
```

### Access the UI

Open http://localhost:7860 in your browser for the Gradio dashboard.

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Linting
make lint

# Format code
make format
```

## 📡 API Endpoints

### A2A Protocol

- `GET /.well-known/agent-card.json` - Agent capabilities
- `POST /tasks/send` - Send a task
- `POST /tasks/sendSubscribe` - Send task with streaming
- `GET /tasks/{task_id}` - Get task status
- `POST /tasks/{task_id}/cancel` - Cancel task
- `GET /health` - Health check

### Example Request

```bash
curl -X POST http://localhost:8000/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "id": "task-1",
    "message": {"role": "user", "content": "Hello"}
  }'
```

## 📚 Documentation

- [PROTOCOLS.md](docs/PROTOCOLS.md) - A2A and MCP protocol details
- [MODELS.md](docs/MODELS.md) - Model configuration and usage
- [BUILD_NOTES.md](docs/BUILD_NOTES.md) - Build and development notes
- [PUBLISH.md](docs/PUBLISH.md) - Publishing and deployment guide

## 🔌 MCP Tools

### Web Search
- `web_search` - Search the web
- `get_page_content` - Fetch page content

### File System
- `read_file` - Read file contents
- `write_file` - Write file contents
- `list_directory` - List directory contents
- `delete_file` - Delete a file

### GitHub
- `search_repositories` - Search repositories
- `get_repository` - Get repository details
- `list_issues` - List repository issues
- `get_readme` - Get README content

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `make test`
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- DeepSeek for the LLM API
- MCP Protocol specification
- A2A Protocol specification
- FastAPI and Gradio communities
