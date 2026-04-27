# Protocol Documentation

## Overview

This agent implements two complementary protocols:

1. **A2A (Agent-to-Agent)**: HTTP-based protocol for agent communication
2. **MCP (Model Context Protocol)**: Stdio-based protocol for tool execution

## A2A Protocol

### Agent Card

The agent card is served at `/.well-known/agent-card.json` and describes:

- **Name**: Agent identifier
- **Description**: What the agent does
- **URL**: Agent endpoint
- **Version**: Semantic version
- **Capabilities**: Supported features (streaming, push notifications)
- **Skills**: Available capabilities
- **Tools**: Available MCP tools

### Task Lifecycle

```
User → POST /tasks/send → Agent → LLM → MCP Tools → Response
```

### Endpoints

#### GET /.well-known/agent-card.json

Returns agent metadata and capabilities.

**Response:**
```json
{
  "name": "A2A MCP Reference Agent",
  "description": "A production-ready dual-protocol agent",
  "url": "http://localhost:8000",
  "version": "0.1.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "research",
      "name": "Research Assistant",
      "description": "Performs research using web search"
    }
  ],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"]
}
```

#### POST /tasks/send

Send a task to the agent.

**Request:**
```json
{
  "id": "task-123",
  "session_id": "session-456",
  "message": {
    "role": "user",
    "content": "Search for Python tutorials"
  },
  "context": [],
  "metadata": {}
}
```

**Response:**
```json
{
  "id": "task-123",
  "session_id": "session-456",
  "status": "completed",
  "result": {
    "content": "I found several Python tutorials...",
    "tool_calls": 1
  },
  "metadata": {
    "usage": {"total_tokens": 150}
  }
}
```

#### POST /tasks/sendSubscribe

Send a task with streaming response (Server-Sent Events).

**Response:**
```
data: {"type": "status", "status": "working"}

data: {"type": "content", "content": "I found"}

data: {"type": "content", "content": " several"}

data: {"type": "status", "status": "completed"}
```

## MCP Protocol

### Server Architecture

Each MCP server runs as a separate process communicating via stdio:

```
Agent Process
    │
    ├──→ Web Search Server (stdio)
    ├──→ File System Server (stdio)
    └──→ GitHub Server (stdio)
```

### Message Format

MCP uses JSON-RPC 2.0 over stdio:

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "web_search",
        "description": "Search the web",
        "inputSchema": {...}
      }
    ]
  }
}
```

### Tool Definition

Tools are defined with JSON Schema:

```json
{
  "name": "web_search",
  "description": "Search the web for information",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query"
      },
      "num_results": {
        "type": "integer",
        "default": 5
      }
    },
    "required": ["query"]
  }
}
```

### Available Tools

#### Web Search Server

**web_search**
- Parameters: `query` (string), `num_results` (integer)
- Returns: JSON array of search results

**get_page_content**
- Parameters: `url` (string)
- Returns: Page content as text

#### File System Server

**read_file**
- Parameters: `path` (string)
- Returns: File contents

**write_file**
- Parameters: `path` (string), `content` (string)
- Returns: Success message

**list_directory**
- Parameters: `path` (string, optional)
- Returns: JSON array of entries

**delete_file**
- Parameters: `path` (string)
- Returns: Success message

#### GitHub Server

**search_repositories**
- Parameters: `query` (string), `per_page` (integer)
- Returns: JSON object with repositories

**get_repository**
- Parameters: `owner` (string), `repo` (string)
- Returns: Repository details

**list_issues**
- Parameters: `owner` (string), `repo` (string), `state` (string)
- Returns: JSON array of issues

**get_readme**
- Parameters: `owner` (string), `repo` (string)
- Returns: README content

## Protocol Integration

### Agent Reasoning Loop

```
1. User sends task via A2A
2. Agent queries LLM with available tools
3. LLM decides to use tools
4. Agent calls MCP servers
5. Results returned to LLM
6. LLM generates final response
7. Response sent via A2A
```

### Tool Name Mapping

To avoid conflicts, tools are prefixed with server name:

- `web_search__web_search`
- `file_system__read_file`
- `github__search_repositories`

### Error Handling

**A2A Errors:**
- 400: Bad Request (missing content)
- 503: Service Unavailable (agent not initialized)
- 500: Internal Server Error

**MCP Errors:**
- Tool not found: Returns error message
- Invalid arguments: Returns error message
- Server disconnect: Reconnects automatically

## Security Considerations

### A2A Security
- Validate all input
- Sanitize user content
- Rate limiting (recommended for production)
- Authentication (not implemented in reference)

### MCP Security
- Path traversal prevention in file system
- API key validation for external services
- Sandboxed execution
- Timeout handling

## References

- [A2A Protocol Specification](https://github.com/google/A2A)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
