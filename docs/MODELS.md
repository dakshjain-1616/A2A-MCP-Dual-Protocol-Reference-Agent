# Model Configuration

## DeepSeek Integration

This agent uses the DeepSeek API for LLM capabilities, specifically the `deepseek-v4-flash` model.

## Configuration

### Environment Variables

```bash
# Required for production
DEEPSEEK_API_KEY=your_api_key_here

# Optional overrides
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
```

### Settings Class

```python
from a2a_mcp_agent.config import get_settings

settings = get_settings()
print(settings.deepseek_model)  # "deepseek-v4-flash"
```

## DeepSeek Client

### Basic Usage

```python
from a2a_mcp_agent.deepseek_client import DeepSeekClient

client = DeepSeekClient()

# Simple completion
response = await client.chat_completion([
    {"role": "user", "content": "Hello"}
])

print(response["choices"][0]["message"]["content"])
```

### With Tools

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]

response = await client.chat_completion(
    messages=[{"role": "user", "content": "Search for Python"}],
    tools=tools,
    tool_choice="auto"
)
```

### Streaming

```python
async for chunk in client.stream_chat_completion(messages):
    print(chunk, end="")
```

## Mock Mode

When `DEEPSEEK_API_KEY` is not set or `MOCK_MODE=true`:

```python
client = DeepSeekClient()  # Automatically uses mock mode

# Returns mock responses without API calls
response = await client.chat_completion(messages)
```

### Mock Response Format

```json
{
  "id": "mock-chat-completion",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "deepseek-v4-flash",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "This is a mock response..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

## Model Parameters

### Chat Completion

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | list | required | Conversation messages |
| `temperature` | float | 0.7 | Sampling temperature |
| `max_tokens` | int | None | Maximum tokens to generate |
| `tools` | list | None | Available tools |
| `tool_choice` | str | "auto" | Tool selection strategy |

### Response Format

```python
{
    "id": str,
    "object": str,
    "created": int,
    "model": str,
    "choices": [{
        "index": int,
        "message": {
            "role": str,
            "content": str | None,
            "tool_calls": list | None
        },
        "finish_reason": str
    }],
    "usage": {
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int
    }
}
```

## Tool Calling

### Tool Call Format

```python
{
    "id": "call_abc123",
    "type": "function",
    "function": {
        "name": "web_search__web_search",
        "arguments": '{"query": "Python tutorials"}'
    }
}
```

### Processing Tool Calls

```python
message = response["choices"][0]["message"]
tool_calls = message.get("tool_calls", [])

for tool_call in tool_calls:
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"])
    
    # Execute tool
    result = await execute_tool(name, args)
    
    # Add to messages
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": result
    })

# Get final response
final = await client.chat_completion(messages)
```

## Error Handling

### Common Errors

```python
from openai import AuthenticationError, RateLimitError

try:
    response = await client.chat_completion(messages)
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded")
except Exception as e:
    print(f"Error: {e}")
```

## Performance Considerations

### Token Limits

- Input: Up to model's context window
- Output: Configurable via `max_tokens`
- Monitor usage in response

### Best Practices

1. **Reuse client**: Create once, reuse for multiple requests
2. **Streaming**: Use for long responses
3. **Mock mode**: Use for testing
4. **Error handling**: Always wrap API calls

## Testing

### Mock Client

```python
@pytest.fixture
def mock_client():
    return DeepSeekClient(api_key=None)

@pytest.mark.asyncio
async def test_completion(mock_client):
    response = await mock_client.chat_completion([
        {"role": "user", "content": "Hello"}
    ])
    assert "choices" in response
```

## References

- [DeepSeek API Documentation](https://platform.deepseek.com/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
