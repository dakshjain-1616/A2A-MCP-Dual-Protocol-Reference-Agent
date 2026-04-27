# A2A + MCP Dual Protocol Reference Agent Plan

## Goal
Build a production-ready reference implementation of an agent that uses MCP for vertical tool integration and A2A for horizontal agent-to-agent communication, using `deepseek-v4-flash`.

## Research Summary
- **A2A Protocol (April 2026)**: Focuses on `/.well-known/agent-card.json` for discovery and standard endpoints for task submission (`/tasks`) and status.
- **MCP (Model Context Protocol)**: Uses the official Python `mcp` SDK. Implementation will use `stdio` transports for modularity.
- **Model**: `deepseek-v4-flash` via `https://api.deepseek.com/v1`.
- **Tech Stack**: Python 3.11+, FastAPI (A2A), Gradio (UI), Pytest (Testing), Ruff/Mypy (Linting).

## Approach
1. **Modular MCP Servers**: Create independent stdio servers for web search, file system, and GitHub.
2. **A2A Server**: FastAPI implementation of the agent-card and task lifecycle.
3. **Agent Core**: Reasoning loop that integrates the DeepSeek client with the MCP client.
4. **Gradio UI**: Real-time visualization of the handshake, tool calls, and reasoning.
5. **Production Tooling**: Makefile, pyproject.toml, and comprehensive tests with a robust mock mode.

## Subtasks
1. **Project Scaffolding**: Create directory structure, `pyproject.toml`, `requirements.txt`, `Makefile`, and `.env.example`. (Expected: Initialized repo with config files)
2. **MCP Servers Implementation**: Build `web_search`, `file_system`, and `github` stdio servers in `src/a2a_mcp_agent/mcp_servers/`. (Expected: 3 working MCP servers)
3. **DeepSeek & MCP Client**: Implement the `deepseek-v4-flash` HTTP client and the `mcp_client.py` to orchestrate tool calls. (Expected: Functional clients with retry/logging)
4. **Agent Logic (`agent.py`)**: Implement the reasoning loop connecting the LLM to MCP tools. (Expected: Agent can process tasks using tools)
5. **A2A Protocol Implementation**: Implement `a2a_server.py` with `agent-card.json` and task endpoints. (Expected: FastAPI server compliant with A2A spec)
6. **Gradio UI (`ui.py`)**: Build the three-panel dashboard for real-time monitoring. (Expected: Working UI on port 7860)
7. **CLI & Integration**: Implement `cli.py` and `Makefile` commands to tie everything together. (Expected: `a2a-mcp-agent serve` works)
8. **Testing & Quality**: Write pytest suite with 10+ tests (mock mode) and run ruff/mypy. (Expected: Zero errors, 100% pass)
9. **Documentation & Publishing**: Create `PROTOCOLS.md`, `MODELS.md`, `BUILD_NOTES.md`, and `PUBLISH.md`. Initialize git. (Expected: All docs and git state ready)

## Deliverables
| File Path | Description |
|-----------|-------------|
| `src/a2a_mcp_agent/a2a_server.py` | FastAPI A2A implementation |
| `src/a2a_mcp_agent/mcp_client.py` | MCP SDK client |
| `src/a2a_mcp_agent/mcp_servers/` | Stdio MCP servers |
| `src/a2a_mcp_agent/ui.py` | Gradio Dashboard |
| `tests/` | Pytest suite |
| `BUILD_NOTES.md` | Execution logs and sample handshake |

## Evaluation Criteria
- A2A `agent-card.json` is valid and served.
- MCP `list_tools` returns correct tools.
- Agent loop completes a research task in mock mode.
- Gradio UI launches and displays streaming data.
- Linting and type-checking pass with zero errors.

## Notes
- Workspace root: `/root/27_all5/projects/a2a-mcp-reference-agent/` (will be mapped from `/app/dual_protocol_agent_0717`).
- Ensure `deepseek-v4-flash` is the only model used.
- No `README.md` generation.
