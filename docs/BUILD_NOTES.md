# Build Notes

## Development Environment

### Prerequisites

- Python 3.11+
- pip or uv
- Git

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"
```

## Project Structure

```
src/a2a_mcp_agent/
├── __init__.py              # Package exports
├── agent.py                 # Core agent orchestration
├── a2a_server.py           # FastAPI A2A server
├── cli.py                  # Click CLI
├── config.py               # Pydantic settings
├── deepseek_client.py     # LLM client
├── mcp_client.py          # MCP orchestration
├── ui.py                   # Gradio dashboard
├── mcp_servers/            # MCP implementations
│   ├── __init__.py
│   ├── web_search.py
│   ├── file_system.py
│   └── github.py
└── utils/
    ├── __init__.py
    └── logging.py         # Structured logging
```

## Key Design Decisions

### 1. Async Architecture

All I/O operations are async:

```python
# Good
async def process_task(self, task: str) -> dict:
    result = await self.llm_client.chat_completion(...)
    return result

# Bad (blocking)
def process_task(self, task: str) -> dict:
    result = requests.post(...)  # Blocking!
    return result
```

### 2. Mock Mode

Everything supports mock mode for testing:

```python
class DeepSeekClient:
    def __init__(self, api_key: str | None = None):
        self.mock_mode = not api_key
        if not self.mock_mode:
            self.client = AsyncOpenAI(...)
```

### 3. Protocol Separation

A2A and MCP are cleanly separated:

- A2A: HTTP/FastAPI for external communication
- MCP: Stdio for tool execution

### 4. Error Handling

Graceful degradation:

```python
try:
    result = await self.mcp_client.call_tool(...)
except Exception as e:
    logger.error(f"Tool error: {e}")
    return {"error": str(e), "success": False}
```

## Testing Strategy

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_config.py          # Settings tests
├── test_deepseek_client.py # LLM client tests
├── test_mcp_client.py      # MCP client tests
├── test_agent.py           # Agent logic tests
├── test_a2a_server.py      # A2A server tests
└── test_mcp_servers.py     # MCP server tests
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/a2a_mcp_agent --cov-report=term-missing

# Specific test
pytest tests/test_agent.py::TestAgent::test_process_task_simple -v
```

### Mock Fixtures

```python
@pytest.fixture
def mock_client() -> MockMCPClient:
    """Create a mock MCP client."""
    return MockMCPClient()

@pytest_asyncio.fixture
async def mock_agent() -> AsyncGenerator[Agent, None]:
    """Create a mock agent for testing."""
    agent = Agent(mock_mode=True)
    await agent.initialize()
    yield agent
    await agent.close()
```

## Code Quality

### Linting

```bash
# Run all linters
make lint

# Individual tools
ruff check src/ tests/
mypy src/a2a_mcp_agent
```

### Formatting

```bash
# Auto-format
make format

# Check only
ruff format --check src/ tests/
```

### Type Checking

```python
# Use type hints everywhere
from typing import Any, AsyncGenerator

async def process_task(
    self,
    task: str,
    context: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    ...
```

## Build Process

### Makefile Targets

```bash
make install        # Production install
make dev-install    # Development install
make test           # Run tests
make lint           # Run linters
make format         # Format code
make serve-a2a      # Start A2A server
make serve-ui       # Start Gradio UI
make serve-mock     # Start all in mock mode
make clean          # Clean build artifacts
```

### Package Building

```bash
# Build wheel
python -m build

# Check package
twine check dist/*
```

## Common Issues

### Import Errors

```bash
# Ensure src is in path
export PYTHONPATH=src:$PYTHONPATH

# Or install in editable mode
pip install -e .
```

### Async Test Failures

```python
# Use pytest-asyncio
import pytest_asyncio

@pytest_asyncio.fixture
async def async_fixture():
    ...
```

### MCP Server Not Found

```bash
# Ensure package is installed
pip install -e .

# Run with module path
python -m a2a_mcp_agent.mcp_servers.web_search
```

## Performance Optimization

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run code
await agent.process_task("test")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Memory Usage

```python
import tracemalloc

tracemalloc.start()

# Run code
await agent.process_task("test")

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f} MB")
print(f"Peak: {peak / 1024 / 1024:.2f} MB")
```

## Debugging

### Logging

```python
from a2a_mcp_agent.utils.logging import get_logger

logger = get_logger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python -m a2a_mcp_agent.a2a_server

# Or in .env
LOG_LEVEL=DEBUG
```

## CI/CD Integration

### GitHub Actions

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: make test
      - run: make lint
```

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Ruff](https://docs.astral.sh/ruff/)
